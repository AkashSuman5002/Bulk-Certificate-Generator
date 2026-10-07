"""Create generation jobs and certificates tables."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    job_status = sa.Enum("pending", "processing", "completed", "completed_with_errors", "failed", name="jobstatus")
    certificate_status = sa.Enum("pending", "completed", "failed", name="certificatestatus")
    job_status.create(op.get_bind(), checkfirst=True)
    certificate_status.create(op.get_bind(), checkfirst=True)
    op.create_table("generation_jobs", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("event_name", sa.String(200), nullable=False), sa.Column("event_date", sa.Date(), nullable=False), sa.Column("organization_name", sa.String(200), nullable=False), sa.Column("signatory_name", sa.String(200), nullable=False), sa.Column("status", job_status, nullable=False), sa.Column("total_count", sa.Integer(), nullable=False), sa.Column("successful_count", sa.Integer(), nullable=False), sa.Column("failed_count", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("started_at", sa.DateTime(timezone=True)), sa.Column("completed_at", sa.DateTime(timezone=True)), sa.Column("error_message", sa.Text()), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_generation_jobs_status", "generation_jobs", ["status"])
    op.create_table("certificates", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("job_id", sa.Uuid(), nullable=False), sa.Column("certificate_id", sa.String(100), nullable=False), sa.Column("recipient_name", sa.String(200), nullable=False), sa.Column("recipient_email", sa.String(320), nullable=False), sa.Column("status", certificate_status, nullable=False), sa.Column("file_path", sa.String(500)), sa.Column("error_message", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("completed_at", sa.DateTime(timezone=True)), sa.ForeignKeyConstraint(["job_id"], ["generation_jobs.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("job_id", "certificate_id", name="uq_certificate_job_identifier"))
    op.create_index("ix_certificates_id", "certificates", ["id"], unique=True)
    op.create_index("ix_certificates_job_id", "certificates", ["job_id"])
    op.create_index("ix_certificates_job_status", "certificates", ["job_id", "status"])


def downgrade() -> None:
    op.drop_table("certificates")
    op.drop_index("ix_generation_jobs_status", table_name="generation_jobs")
    op.drop_table("generation_jobs")
    sa.Enum(name="certificatestatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="jobstatus").drop(op.get_bind(), checkfirst=True)