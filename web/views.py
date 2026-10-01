# ============================================================
# DEFAULT INITIAL PASSWORD
# ============================================================

DEFAULT_LEADER_PASSWORD = "adminictclub@2026"


# ============================================================
# ENSURE ICT CLUB LEADER ACCOUNTS EXIST
# ============================================================

def ensure_club_users():
    """
    Create all ICT Club leadership accounts automatically.

    ALL leadership accounts use:

        adminictclub@2026

    This password is also applied to existing leadership
    accounts so that previously created accounts can log in.
    """

    user_model = get_user_model()

    leader_accounts = [
        ("codestar", ["President"]),
        ("patron", ["Patron"]),
        ("secretary", ["Secretary"]),
        ("speaker", ["Speaker"]),
        ("treasurer", ["Treasurer"]),
        ("projectsmanager", ["Projects Manager"]),
        ("mobiliser", ["Mobiliser / Coordinator"]),
    ]

    for username, group_names in leader_accounts:

        # ----------------------------------------------------
        # Create groups
        # ----------------------------------------------------

        group_objs = []

        for group_name in group_names:

            group, _ = Group.objects.get_or_create(
                name=group_name
            )

            group_objs.append(group)

        # ----------------------------------------------------
        # Create or retrieve user
        # ----------------------------------------------------

        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={
                "is_staff": username in {
                    "codestar",
                    "patron",
                },
                "is_active": True,
            },
        )

        # ----------------------------------------------------
        # Make sure account is active
        # ----------------------------------------------------

        user.is_active = True

        # President and Patron can access Django admin
        user.is_staff = username in {
            "codestar",
            "patron",
        }

        # ----------------------------------------------------
        # SET PASSWORD
        # ----------------------------------------------------
        #
        # IMPORTANT:
        # The password is deliberately reset here every time
        # ensure_club_users() runs.
        #
        # Therefore all seven leadership accounts will use:
        #
        # adminictclub@2026
        #
        # ----------------------------------------------------

        user.set_password(
            DEFAULT_LEADER_PASSWORD
        )

        user.save(
            update_fields=[
                "password",
                "is_active",
                "is_staff",
            ]
        )

        # ----------------------------------------------------
        # Assign leadership group
        # ----------------------------------------------------

        user.groups.set(
            group_objs
        )

        logger.info(
            "ICT Club leader account synchronized: %s",
            username,
        )
