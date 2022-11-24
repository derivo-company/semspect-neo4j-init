from dataclasses import dataclass
import logging

from neo4j.exceptions import Neo4jError, DriverError

logging.basicConfig()
logger = logging.getLogger("init_semspect")
logger.setLevel(level=logging.INFO)


@dataclass(frozen=True)
class SemspectProcedure:
    """A Semspect procedure that can be called. Note: A semspect procedure has a name and an expected status code
    that can be checked """
    name: str
    expected_status_code: int

    def create_call(self):
        return f'CALL {self.name}'


@dataclass(frozen=True)
class Configuration:
    """What configuration should be called for what user on what database"""
    user: str
    database: str


class SemspectProcedures:
    """Predefined list of semspect procedures"""
    SEMSPECT_INIT = SemspectProcedure('semspect.init', 200)
    SEMSPECT_INIT_NO_WRITE = SemspectProcedure(f'{SEMSPECT_INIT.name}NoWrite', 200)
    SEMSPECT_RELOAD = SemspectProcedure('semspect.reload', 200)
    SEMSPECT_RELOAD_NO_WRITE = SemspectProcedure(f'{SEMSPECT_RELOAD.name}NoWrite', 200)


def run_configurations(driver_factory, configurations):
    """Run given configurations with given driver
    :param driver_factory : driver_factory returning a Neo4jDriver
    :param configurations: List of configurations to run
    :returns a list of configurations that weren't executed successfully
     """
    faulty_configurations = []
    with driver_factory() as driver:
        for i, configuration in enumerate(configurations):
            logger.info(f'Running configuration {i + 1}/{len(configurations)}. Configuration: {configuration}')
            if not _run_configuration(driver, configuration):
                faulty_configurations.append(configuration)
    return faulty_configurations


def _run_configuration(driver, configuration):
    """Run one configuration with given driver"""
    with driver.session(database=configuration.database, impersonated_user=configuration.user) as session:
        # we first suppose the user has write-privileges (necessary for semspect labels) and try a simple reload.
        # if this succeeds either reload was not necessary or it worked
        # if it does not succeed, we try again without write privileges
        # if this also fails, we try the initialisation first with, then without write privileges
        logger.info(f'Trying reload...')
        if _run_procedure(session, SemspectProcedures.SEMSPECT_RELOAD):
            # reload worked with write privileges
            logger.info(f'Done.')
            return True
        logger.info(f'Trying reload without write privileges...')
        if _run_procedure(session, SemspectProcedures.SEMSPECT_RELOAD_NO_WRITE):
            # reload worked without write privileges
            logger.info(f'Done.')
            return True
        logger.info(f'Trying init...')
        if _run_procedure(session, SemspectProcedures.SEMSPECT_INIT):
            # init worked with write privileges
            logger.debug(f'Done.')
            return True
        logger.info(f'Trying init without write privileges...')
        if _run_procedure(session, SemspectProcedures.SEMSPECT_INIT_NO_WRITE):
            # init worked without write privileges
            logger.info(f'Done.')
            return True
        # as well reload as init failed both with and without write privileges
        logger.info(f'Configuration {configuration} failed')
        return False


def _run_procedure(session, procedure):
    try:
        record = session.run(procedure.create_call()).single()
        logger.debug(f'Received answer {record}')
        status_code = record['status']
        if status_code != procedure.expected_status_code:
            logger.debug(
                f'Returned status {status_code} code did not match expected {procedure.expected_status_code}.'
                f'Error: {record["errors"]}')
            return False
        return True
    except (Neo4jError, DriverError) as err:
        logger.error(f'Received neo4j error {err}')
        return False
