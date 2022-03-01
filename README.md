# init_semspect

Simple python script that demonstrates how the semspect init can be triggered for different users.

## Use Case

On the first connection of a user to the semspect-neo4j-plugin it has to analyse the current DBMS. Depending on the size
of the database this initialization process can take seconds, minutes or hours. Note that because of the
fine-grained-access-control this process has to be done for each user individually. Also, the initialization process has
to be done after each update of the database.

## How it works

We utilize the impersonate feature that was introduced in neo4j
4.4 : https://neo4j.com/docs/cypher-manual/current/access-control/dbms-administration/#access-control-dbms-administration-impersonation
From https://neo4j.com/docs/cypher-manual/current/access-control/dbms-administration/#access-control-dbms-administration-impersonation:
> The DBMS privileges for impersonation are assignable using Cypher administrative commands.
> They can be granted, denied, and revoked like other privileges.
> Impersonation is the capability of a user to assume another user’s roles (and therefore privileges),
> with the restriction of not being able to execute updating admin commands as the impersonated user
> (i.e. they would still be able to use SHOW commands). This feature allows an user to run queries

In practice this means that we grant one the user the right to impersonate all semspectUsers that we want to initialize.

## System Requirements

* python 3.8 (or later)
* poetry (for dependency management): https://python-poetry.org/docs/
* neo4j server 4.4 (or later)

## Usage

### Setup Neo4j

1. Create an `initUser` : This will be the user that impersonates the semspect users. 
`CREATE USER initUser SET PLAINTEXT PASSWORD 'secret_password' CHANGE NOT REQUIRED`
2. Create an `semspectImpersonatorRole` role: `CREATE ROLE semspectImpersonatorRole`
3. Grant the `semspectImpersonatorRole` role to the `initUser`: `GRANT ROLE semspectImpersonatorRole TO initUser`
4. Grant impersonate privilege for all semspect users to the `semspectImpersonatorRole` role:
`GRANT IMPERSONATE ($SEMSPECT_USER1[,...]) ON DBMS TO semspectImpersonatorRole`

### Running the script

```shell
# We use poetry 
## to install the dependencies
poetry install
##to run the script
poetry run run_example
```

