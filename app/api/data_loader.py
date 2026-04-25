"""
Data loader script to populate PostgreSQL database with Neurobagel data.

This script provides utilities to load data from various sources (JSON, CSV, etc.)
into the PostgreSQL database using SQLModel ORM.

Usage:
    python -m app.api.data_loader --help
"""

import argparse
import asyncio
import json
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, select

from .database import engine
from .db_models import (
    Acquisition,
    CompletedPipeline,
    ControlledTerm,
    ControlledTermAttribute,
    Dataset,
    Session,
    Subject,
)


async def load_from_json(json_path: Path, db_session: AsyncSession):
    """
    Load data from a JSON file into the database.
    
    Expected JSON structure:
    {
        "datasets": [
            {
                "dataset_uuid": "uuid",
                "dataset_name": "name",
                "subjects": [
                    {
                        "sub_id": "sub-01",
                        "sessions": [
                            {
                                "session_id": "ses-01",
                                "session_type": "ImagingSession",
                                "age": 25.5,
                                "sex": "snomed:248152002",
                                "acquisitions": [...],
                                "pipelines": [...]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    """
    with open(json_path, "r") as f:
        data = json.load(f)
    
    for dataset_data in data.get("datasets", []):
        # Create dataset
        dataset = Dataset(
            dataset_uuid=dataset_data["dataset_uuid"],
            dataset_name=dataset_data["dataset_name"],
            dataset_portal_uri=dataset_data.get("dataset_portal_uri"),
            authors=json.dumps(dataset_data.get("authors", [])),
            homepage=dataset_data.get("homepage"),
            references_and_links=json.dumps(dataset_data.get("references_and_links", [])),
            keywords=json.dumps(dataset_data.get("keywords", [])),
            repository_url=dataset_data.get("repository_url"),
            access_instructions=dataset_data.get("access_instructions"),
            access_type=dataset_data.get("access_type"),
            access_email=dataset_data.get("access_email"),
            access_link=dataset_data.get("access_link"),
        )
        db_session.add(dataset)
        await db_session.flush()  # Get dataset ID
        
        for subject_data in dataset_data.get("subjects", []):
            # Create subject
            subject = Subject(
                sub_id=subject_data["sub_id"],
                dataset_id=dataset.id,
            )
            db_session.add(subject)
            await db_session.flush()  # Get subject ID
            
            for session_data in subject_data.get("sessions", []):
                # Create session
                session = Session(
                    session_id=session_data["session_id"],
                    session_type=session_data.get("session_type", "PhenotypicSession"),
                    subject_id=subject.id,
                    age=session_data.get("age"),
                    sex=session_data.get("sex"),
                    diagnosis=session_data.get("diagnosis"),
                    subject_group=session_data.get("subject_group"),
                    assessment=session_data.get("assessment"),
                    session_file_path=session_data.get("session_file_path"),
                )
                db_session.add(session)
                await db_session.flush()  # Get session ID
                
                # Create acquisitions
                for acq_data in session_data.get("acquisitions", []):
                    acquisition = Acquisition(
                        session_id=session.id,
                        image_modal=acq_data["image_modal"],
                    )
                    db_session.add(acquisition)
                
                # Create pipelines
                for pipe_data in session_data.get("pipelines", []):
                    pipeline = CompletedPipeline(
                        session_id=session.id,
                        pipeline_name=pipe_data["pipeline_name"],
                        pipeline_version=pipe_data["pipeline_version"],
                    )
                    db_session.add(pipeline)
    
    await db_session.commit()
    print(f"Successfully loaded data from {json_path}")


async def clear_database(db_session: AsyncSession):
    """Clear all data from the database."""
    # Delete in reverse order of dependencies
    await db_session.execute("DELETE FROM completed_pipelines")
    await db_session.execute("DELETE FROM acquisitions")
    await db_session.execute("DELETE FROM sessions")
    await db_session.execute("DELETE FROM subjects")
    await db_session.execute("DELETE FROM datasets")
    await db_session.execute("DELETE FROM controlled_terms")
    await db_session.execute("DELETE FROM controlled_term_attributes")
    await db_session.commit()
    print("Database cleared")


async def main():
    """Main function to run data loader."""
    parser = argparse.ArgumentParser(
        description="Load data into Neurobagel PostgreSQL database"
    )
    parser.add_argument(
        "--json",
        type=Path,
        help="Path to JSON file containing data to load",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear all data from database before loading",
    )
    
    args = parser.parse_args()
    
    # Create async session
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        if args.clear:
            await clear_database(session)
        
        if args.json:
            await load_from_json(args.json, session)


if __name__ == "__main__":
    asyncio.run(main())
