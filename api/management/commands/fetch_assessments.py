import requests
import base64
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from assessments.models import Assessment
from engine.services.cq_dsf import run_engine

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fetches new assessment payloads from Unity Cloud Save and runs the CQ-DSF engine on each one.'

    def get_auth_header(self):
        """
        Uses the static Authorization header provided by the Unity team.
        Stored in .env as UNITY_AUTH_HEADER — never hardcoded here.
        """
        return {
        "Authorization": settings.UNITY_AUTH_HEADER,
        "Content-Type": "application/json"}

    def get_all_player_ids(self, headers):
        """
        Fetches all player IDs that have saved data in the Unity project.
        Uses the Unity Cloud Save admin endpoint to list players.
        """
        url = (
            f"https://services.api.unity.com/cloud-save/v1/data/projects/"
            f"{settings.UNITY_PROJECT_ID}/environments/"
            f"{settings.UNITY_ENVIRONMENT_ID}/players"
        )

        player_ids = []

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            player_ids = [player['id'] for player in data.get('results', [])]
            self.stdout.write(f"Found {len(player_ids)} players in Unity Cloud Save.")
        except Exception as e:
            logger.error(f"Failed to fetch player list: {e}")
            self.stdout.write(self.style.ERROR(f"Failed to fetch player list: {e}"))

        return player_ids

    def get_player_data(self, player_id, headers):
        """
        Fetches the saved assessment payload for a specific player.
        """
        url = (
            f"https://services.api.unity.com/cloud-save/v1/data/projects/"
            f"{settings.UNITY_PROJECT_ID}/environments/"
            f"{settings.UNITY_ENVIRONMENT_ID}/players/{player_id}/items"
        )

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch data for player {player_id}: {e}")
            self.stdout.write(self.style.ERROR(f"Failed to fetch data for player {player_id}: {e}"))
            return None

    def is_already_processed(self, session_id):
        """
        Checks if this session has already been processed.
        Uses session_id as the unique identifier to avoid duplicate processing.
        """
        return Assessment.objects.filter(session_id=session_id).exists()

    def handle(self, *args, **options):
        """
        Main entry point. Called when you run:
        python manage.py fetch_assessments
        """
        self.stdout.write("Starting Unity Cloud Save fetch...")

        headers = self.get_auth_header()
        player_ids = self.get_all_player_ids(headers)

        if not player_ids:
            self.stdout.write("No players found. Exiting.")
            return

        processed = 0
        skipped = 0
        failed = 0

        for player_id in player_ids:
            data = self.get_player_data(player_id, headers)

            if not data:
                failed += 1
                continue

            for item in data.get('results', []):
                try:
                    payload = item.get('value')

                    if not payload:
                        continue

                    # payload arrives as a dict from Unity Cloud Save
                    # if it arrives as a string, parse it
                    if isinstance(payload, str):
                        import json
                        payload = json.loads(payload)

                    session_id = payload.get('session_id')

                    if not session_id:
                        self.stdout.write(self.style.WARNING(
                            f"Player {player_id}: payload missing session_id, skipping."
                        ))
                        failed += 1
                        continue

                    # skip if already processed
                    if self.is_already_processed(session_id):
                        self.stdout.write(f"Session {session_id} already processed, skipping.")
                        skipped += 1
                        continue

                    # save the assessment
                    assessment = Assessment.objects.create(
                        test_taker_id=payload.get('test_taker_id'),
                        session_id=session_id,
                        assessment_version=payload.get('assessment_version', 'v1.0'),
                        raw_payload=payload
                    )

                    self.stdout.write(f"Saved assessment for session {session_id}.")

                    # run the engine
                    self.stdout.write(f"Running CQ-DSF engine for assessment {assessment.id}...")
                    recommendation = run_engine(assessment_id=assessment.id)
                    self.stdout.write(self.style.SUCCESS(
                        f"Recommendation generated: {recommendation}"
                    ))

                    processed += 1

                except Exception as e:
                    logger.error(f"Failed to process item for player {player_id}: {e}")
                    self.stdout.write(self.style.ERROR(
                        f"Failed to process item for player {player_id}: {e}"
                    ))
                    failed += 1

        self.stdout.write("---")
        self.stdout.write(self.style.SUCCESS(f"Processed: {processed}"))
        self.stdout.write(self.style.WARNING(f"Skipped (already done): {skipped}"))
        self.stdout.write(self.style.ERROR(f"Failed: {failed}"))
        self.stdout.write("Done.")