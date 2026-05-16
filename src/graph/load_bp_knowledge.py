"""
Script para cargar la base de conocimiento (BP entities y relationships) en Neo4j.

Uso:
    python src/graph/load_bp_knowledge.py [--uri bolt://localhost:7687] [--user neo4j] [--password password]

Prerrequisitos:
    - Neo4j debe estar ejecutándose (e.g., docker compose -f docker/docker-compose.yml up -d neo4j)
    - Las credenciales deben ser correctas en variables de entorno o como argumentos
"""

import json
import argparse
from pathlib import Path
from neo4j import GraphDatabase
from loguru import logger

# Configure logging
logger.remove()
logger.add(lambda msg: print(msg, end=""), colorize=True)


class BPKnowledgeLoader:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.session = None
        
    def connect(self):
        """Test connection to Neo4j"""
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("✅ Connected to Neo4j successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            return False
    
    def clear_database(self):
        """Clear all nodes and relationships (WARNING: destructive)"""
        try:
            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
            logger.info("✅ Database cleared")
        except Exception as e:
            logger.error(f"❌ Error clearing database: {e}")
    
    def load_entities(self, entities_file="data/processed/bp_entities.json"):
        """Load entities as Neo4j nodes"""
        with open(entities_file) as f:
            data = json.load(f)
        
        with self.driver.session() as session:
            # Load components
            for component in data['entity_types']['components']:
                session.run("""
                    MERGE (c:COMPONENTE {name: $name})
                    SET c.description = $description,
                        c.category = $category,
                        c.aliases = $aliases
                """,
                name=component['name'],
                description=component['description'],
                category=component['category'],
                aliases=component.get('alias', [])
                )
            
            logger.info(f"✅ Loaded {len(data['entity_types']['components'])} components")
            
            # Load technical concepts
            for concept in data['entity_types']['technical_concepts']:
                session.run("""
                    MERGE (t:CONCEPTO {name: $name})
                    SET t.description = $description,
                        t.category = $category,
                        t.aliases = $aliases
                """,
                name=concept['name'],
                description=concept['description'],
                category=concept['category'],
                aliases=concept.get('alias', [])
                )
            
            logger.info(f"✅ Loaded {len(data['entity_types']['technical_concepts'])} technical concepts")
            
            # Load vehicle segments
            for segment in data['entity_types']['vehicle_segments']:
                session.run("""
                    MERGE (s:SEGMENTO {name: $name})
                    SET s.description = $description
                """,
                name=segment['name'],
                description=segment['description']
                )
            
            logger.info(f"✅ Loaded {len(data['entity_types']['vehicle_segments'])} vehicle segments")
    
    def load_relationships(self, relationships_file="data/processed/bp_relationships.json"):
        """Load relationships using Cypher format from JSON"""
        with open(relationships_file) as f:
            data = json.load(f)
        
        with self.driver.session() as session:
            for rel in data['relationships']:
                source = rel['source']
                target = rel['target']
                rel_type = rel['relationship']
                
                # Map source and target to appropriate labels
                source_label = "COMPONENTE"  # Default
                target_label = "COMPONENTE"  # Default
                
                # Create relationship
                cypher = f"""
                    MATCH (s {{name: $source}})
                    MATCH (t {{name: $target}})
                    CREATE (s)-[:{rel_type}]->(t)
                """
                
                try:
                    session.run(cypher, source=source, target=target)
                except Exception as e:
                    # Try to match without labels if first attempt fails
                    logger.warning(f"⚠️  Could not create relationship {rel['id']}: {e}")
            
            logger.info(f"✅ Loaded {len(data['relationships'])} relationships")
    
    def load_chunks(self, chunks_file="data/processed/bp_chunks.json"):
        """Load knowledge chunks as nodes"""
        with open(chunks_file) as f:
            data = json.load(f)
        
        with self.driver.session() as session:
            for chunk in data['chunks']:
                session.run("""
                    MERGE (c:CHUNK {id: $id})
                    SET c.title = $title,
                        c.content = $content,
                        c.category = $category,
                        c.priority = $priority,
                        c.bp_reference = $bp_reference,
                        c.keywords = $keywords
                """,
                id=chunk['id'],
                title=chunk['title'],
                content=chunk['content'],
                category=chunk['category'],
                priority=chunk['priority'],
                bp_reference=chunk.get('bp_reference', ''),
                keywords=chunk.get('keywords', [])
                )
            
            logger.info(f"✅ Loaded {len(data['chunks'])} knowledge chunks")
    
    def close(self):
        """Close Neo4j driver"""
        if self.driver:
            self.driver.close()
            logger.info("✅ Neo4j connection closed")


def main():
    parser = argparse.ArgumentParser(
        description="Load GM Best Practices knowledge base into Neo4j"
    )
    parser.add_argument('--uri', default='bolt://localhost:7687', 
                       help='Neo4j connection URI')
    parser.add_argument('--user', default='neo4j', 
                       help='Neo4j username')
    parser.add_argument('--password', default='admin', 
                       help='Neo4j password')
    parser.add_argument('--no-clear', action='store_true',
                       help='Do not clear existing data before loading')
    
    args = parser.parse_args()
    
    logger.info(f"🚀 Starting BP Knowledge Base Loader...")
    logger.info(f"   URI: {args.uri}")
    
    loader = BPKnowledgeLoader(args.uri, args.user, args.password)
    
    try:
        # Test connection
        if not loader.connect():
            logger.error("Cannot connect to Neo4j. Make sure it's running:")
            logger.info("   docker compose -f docker/docker-compose.yml up -d neo4j")
            return
        
        # Clear database if requested
        if not args.no_clear:
            confirm = input("⚠️  Clear existing data? (y/n): ")
            if confirm.lower() == 'y':
                loader.clear_database()
        
        # Load data
        logger.info("📦 Loading entities...")
        loader.load_entities()
        
        logger.info("📦 Loading chunks...")
        loader.load_chunks()
        
        logger.info("📦 Loading relationships...")
        loader.load_relationships()
        
        logger.info("✅ Knowledge base loaded successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        loader.close()


if __name__ == "__main__":
    main()
