from typing import List, Optional
from sqlalchemy.types import TypeDecorator, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String


class StringList(TypeDecorator):
    """
    Cross-database list[str] type.
    - PostgreSQL: ARRAY(TEXT)
    - SQLite / others: JSON
    """
    
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(ARRAY(String))
        return dialect.type_descriptor(JSON)

    def process_bind_param(
        self,
        value: Optional[List[str]],
        dialect,
    ):
        if value is None:
            return []

        if not isinstance(value, list):
            raise ValueError("StringList value must be a list of strings")

        # Enforce str items
        return [str(v) for v in value]

    def process_result_value(
        self,
        value,
        dialect,
    ):
        if value is None:
            return []
        return list(value)
