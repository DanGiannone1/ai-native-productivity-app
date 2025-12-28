"""Quick script to check what data is in Cosmos DB."""
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from productivity_mcp.cosmos_client import get_container

container = get_container()
items = list(container.query_items(
    'SELECT c.id, c.docType, c.entityType FROM c',
    enable_cross_partition_query=True
))

schemas = [i for i in items if i.get('docType') == 'schema']
entities = [i for i in items if i.get('docType') == 'entity']

print(f"Schemas: {len(schemas)}")
print(f"\nEntities by type:")
entity_types = {}
for e in entities:
    et = e.get('entityType', 'unknown')
    entity_types[et] = entity_types.get(et, 0) + 1

for et, count in sorted(entity_types.items()):
    print(f"  {et}: {count}")

print(f"\nTotal entities: {len(entities)}")
print(f"Total documents: {len(items)}")
