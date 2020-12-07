# Configuring access to your account

## Get a Hypothes.is developer key

Sign in to your Hypothes.is account and [generate a personal API token](https://hypothes.is/account/developer).

![Hypothesis screen with an API token](assets\image-20201129174451232.png)

Create a file named `.env` and copy the token as follows:

```text
HYP_KEY="my-very-very-very-secret-token"
```

## Get a RemNote developer key and user id

Sign in to your RemNote account and [generate a personal API token](https://www.remnote.io/api_keys).

![image-20201129181917522](assets\image-20201129181917522.png)

Copy the generated key to a new line in the `.env` file
(you will see the key only once; copy it before confirming):

```text
REM_KEY="my-other-quite-secret-token"
```

Once the key is created, it will appear in the the Backend API
Keys table. Copy the value in the second column (`User ID`) and
place it in the same `.env` file.

```text
REM_USERID="my-really-random-id"
```

## Add generated keys and ID to the environment

To add the variables to the local environment, go to the folder
where `.env` file is placed and run in a terminal:

```bash
source .env
```
