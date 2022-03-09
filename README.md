# init_semspect

A python script that demonstrates how to trigger SemSpect initialization for different users.

## Use Case

On the first connection of a user to a database the semspect-neo4j-plugin will automatically initialize and set up for this particular user/database pair (determine the label hierarchy, re-compute SemSpect labels, etc.). Depending on the size of the database this initialization process can take seconds, minutes or hours. In addition, the initialization process has to be re-done after each update of the database.

With the help of this python script the administrators of a SemSpect server installation can trigger such (re-)initializations for any pair of user/database on demand.

## How it works

We utilize the [DBMS impersonate](https://neo4j.com/docs/cypher-manual/current/access-control/dbms-administration/#access-control-dbms-administration-impersonation) feature introduced in Neo4j
4.4 : 
> The DBMS privileges for impersonation are assignable using Cypher administrative commands.
> They can be granted, denied, and revoked like other privileges.
> Impersonation is the capability of a user to assume another user’s roles (and therefore privileges),
> with the restriction of not being able to execute updating admin commands as the impersonated user
> (i.e. they would still be able to use SHOW commands). This feature allows an user to run queries

In practice this means that we grant one dedicated (technical) user the right to impersonate all SemSpect users that we want to initialize. See section [Usage](#usage) on how to create such an inmpersonate user and [example.py](https://github.com/derivo-company/semspect-neo4j-init/blob/develop/example.py) for an examply how to trigger initializations.

## System Requirements

* python 3.8 (or later)
* poetry (for dependency management): https://python-poetry.org/docs/
* neo4j-enterprise-server 4.4 (or later).
* semspect-server-installation: https://doc.semspect.de/docs/neo4j-graph-app/server-configuration/

(The Neo4j community edition is not supported because there are no roles in the Neo4j community edition)

## Usage

### Setup Neo4j

1. Create an `initUser` : This will be the user that impersonates the SemSpect users. 
`CREATE USER initUser SET PLAINTEXT PASSWORD 'secret_password' CHANGE NOT REQUIRED`
2. Create an `semspectImpersonatorRole` role: `CREATE ROLE semspectImpersonatorRole`
3. Grant the `semspectImpersonatorRole` role to the `initUser`: `GRANT ROLE semspectImpersonatorRole TO initUser`
4. Grant impersonate privilege for all SemSpect users to the `semspectImpersonatorRole` role:
`GRANT IMPERSONATE ($SEMSPECT_USER1[,...]) ON DBMS TO semspectImpersonatorRole`

### Configuration of initialization tasks

1. Specify the Neo4j DBMS and impersonate as part of the Neo4j driver connection:
`GraphDatabase.driver('neo4j://localhost:7687', auth=('initUser', 'secret_password'))`
2. Specify the user/database pairs you want to (re-)initialize in your list of configurations:
`Configuration(procedure=SemspectProcedures.SEMSPECT_INIT, user="Alice", database="neo4j")`

### Running the script

```shell
# We use poetry 
## to install the dependencies
poetry install
##to run the script
poetry run run_example
```

