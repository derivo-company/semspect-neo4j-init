from dataclasses import dataclass
import logging

from neo4j.exceptions import Neo4jError, DriverError

logging.basicConfig()
logger = logging.getLogger("init_semspect")
logger.setLevel(level=logging.INFO)


@dataclass(frozen=True)
class UserType:
    type: str


class UserTypes:
    READ_ONLY = UserType("READ_ONLY")
    READ_WRITE = UserType("READ_WRITE")


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
    user_type: UserType
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
    logger.debug(f'Running configuration {configuration}')
    with driver.session(database=configuration.database, impersonated_user=configuration.user) as session:
        reload_procedure, init_procedure = _user_type_to_semspect_procedures(configuration.user_type)
        if _run_procedure(session, reload_procedure):
            # reload worked (Status code 200).
            # This covers two cases: Either there was no reload necessary because the data didn't change since
            # last initialization or reload worked.
            return True
        if _run_procedure(session, init_procedure):
            # init worked (Status code 200):
            # This covers two cases: init was performed, or init was not necessary
            return True
        # both (reload and init) failed for some reason.
        return False


def _user_type_to_semspect_procedures(user_type):
    """Maps an UserType to one reload and one init function"""
    if user_type == UserTypes.READ_WRITE:
        return SemspectProcedures.SEMSPECT_RELOAD, SemspectProcedures.SEMSPECT_INIT
    if user_type == UserTypes.READ_ONLY:
        return SemspectProcedures.SEMSPECT_RELOAD_NO_WRITE, SemspectProcedures.SEMSPECT_INIT_NO_WRITE
    else:
        raise RuntimeError(f'Unknown user type {user_type}')


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
