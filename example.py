import logging
import sys

from neo4j import GraphDatabase, Neo4jDriver

import init_semspect
from init_semspect import Configuration, SemspectProcedures

logging.basicConfig()
logger = logging.getLogger("init_semspect")
logger.setLevel(level=logging.INFO)


def main():
    example_configurations = [
        # call init for user alice on database neo4j
        Configuration(procedure=SemspectProcedures.SEMSPECT_INIT, user="Alice", database="neo4j"),
        # call init for user bob that has no write privileges on neo4j database
        Configuration(procedure=SemspectProcedures.SEMSPECT_INIT_NO_WRITE, user="Bob", database="neo4j"),
        # call reload for user Charly
        Configuration(procedure=SemspectProcedures.SEMSPECT_RELOAD, user="Charly", database="neo4j"),
        # call reload for user  Derek that has no write privileges
        Configuration(procedure=SemspectProcedures.SEMSPECT_RELOAD, user="Derek", database="neo4j")
    ]

    # hard coded driver_factory that connects as our impersonate user 'initUser'
    def driver_factory() -> Neo4jDriver:
        return GraphDatabase.driver('neo4j://localhost:7687', auth=('initUser', 'my_secret'))

    # run given configurations with given neo4jDriver. The run_configurations method returns a set of configurations that were not executed successfully
    faulty_configurations = init_semspect.run_configurations(driver_factory, example_configurations)
    if not faulty_configurations:
        logger.info('All Configurations succeeded')
        sys.exit(0)
    else:
        logger.error(f'There were {len(faulty_configurations)} errors during the execution of following '
                     f'configurations: {faulty_configurations}')
        sys.exit(255)


if __name__ == '__main__':
    main()
