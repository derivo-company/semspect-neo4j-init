import sys

from neo4j import GraphDatabase, Neo4jDriver
from dataclasses import dataclass
import logging

from neo4j.exceptions import Neo4jError

logging.basicConfig()
logger = logging.getLogger("init_semspect")
logger.setLevel(level=logging.INFO)


@dataclass(frozen=True)
class Neo4jProcedure:
    name: str
    expected_status_code: int

    def create_call(self):
        return f'CALL {self.name}'


@dataclass(frozen=True)
class Configuration:
    procedure: Neo4jProcedure
    user: str
    database: str


# List of semspect procedure definitions
SEMSPECT_INIT = Neo4jProcedure('semspect.init', 200)
SEMSPECT_INIT_NO_WRITE = Neo4jProcedure(f'{SEMSPECT_INIT.name}NoWrite', 200)
SEMSPECT_RELOAD = Neo4jProcedure('semspect.reload', 200)
SEMSPECT_RELOAD_NO_WRITE = Neo4jProcedure(f'{SEMSPECT_RELOAD.name}NoWrite', 200)


def main():
    configurations = [
        Configuration(procedure=SEMSPECT_INIT, user="Alice", database="neo4j"),
        Configuration(procedure=SEMSPECT_INIT_NO_WRITE, user="Bob", database="neo4j")
    ]
    if _run_configurations(configurations):
        sys.exit(0)
    sys.exit(255)


def _run_configurations(configurations):
    """Run given configurations"""
    faulty_configurations = []
    with _create_driver() as driver:
        for i, configuration in enumerate(configurations):
            logger.info(f'Running configuration {i + 1}/{len(configurations)}. Configuration: {configuration}')
            if not _run_configuration(driver, configuration):
                faulty_configurations.append(configuration)

    if not faulty_configurations:
        logger.info('All Configurations succeeded')
        return True
    else:
        logger.error(f'There were {len(faulty_configurations)} errors during the execution of following '
                     f'configurations: {faulty_configurations}')
        return False


def _run_configuration(driver: Neo4jDriver, configuration: Configuration):
    """Run one configuration with given driver"""
    logger.debug(f'Running configuration {configuration}')
    with driver.session(database=configuration.database, impersonated_user=configuration.user) as session:
        return _run_procedure(session, configuration.procedure)


def _run_procedure(session, procedure):
    try:
        record = session.run(procedure.create_call()).single()
        logger.debug(f'Received answer {record}')
        status_code = record['status']
        if status_code != procedure.expected_status_code:
            logger.error(
                f'Returned status {status_code} code did not match expected {procedure.expected_status_code}.'
                f'Error: {record["errors"]}')
            return False
        return True
    except Neo4jError as err:
        logger.error(f'Received neo4j error {err}')
        return False


def _create_driver() -> Neo4jDriver:
    """Utility method to create a connection to neo4j"""
    return GraphDatabase.driver('neo4j://localhost:7687', auth=('initUser', 'b'))


if __name__ == '__main__':
    main()
