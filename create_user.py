#!/usr/bin/env python3

import argparse
from botocore.exceptions import ClientError
from aws_local import client

def main():
    parser = argparse.ArgumentParser(
        description="Créer un utilisateur IAM LocalStack et générer ses clés."
    )
    parser.add_argument(
        "--user",
        required=True,
        help="Nom de l'utilisateur IAM à créer"
    )
    args = parser.parse_args()
    user_name = args.user

    # Création du client IAM
    iam = client("iam")

    # -------------------------------------------------------
    # Création de l'utilisateur IAM
    # -------------------------------------------------------
    print(f"Création de l'utilisateur IAM '{user_name}'…")
    try:
        iam.create_user(UserName=user_name)
        print("✔ Utilisateur créé.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "EntityAlreadyExists":
            print("ℹ Utilisateur déjà existant — OK.")
        else:
            raise e

    # -------------------------------------------------------
    # Création du couple AccessKey / SecretKey
    # -------------------------------------------------------
    print("Génération des clés d'accès…")
    keys = iam.create_access_key(UserName=user_name)
    access_key = keys["AccessKey"]["AccessKeyId"]
    secret_key = keys["AccessKey"]["SecretAccessKey"]
    print("")

    print("Identifiants générés :")
    print(f"  AWS_ACCESS_KEY_ID = {access_key}")
    print(f"  AWS_SECRET_ACCESS_KEY = {secret_key}\n")

if __name__ == "__main__":
    main()

