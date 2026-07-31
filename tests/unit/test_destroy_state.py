"""""""""

Unit tests for macro destroy: interactive confirmation + state cleanup.

Unit tests for macro destroy: interactive confirmation + state cleanup.Unit tests for local + remote state cleanup during macro destroy.

Scenarios covered

─────────────────

Confirmation helpers

 A. _get_destroy_scope — no flags    → "all resources"Scenarios coveredScenarios covered

 B. _get_destroy_scope — --include   → "resources: <list>"

 C. _get_destroy_scope — --exclude   → "all resources except: <list>"──────────────────────────────────

 D. _confirm_destroy  — skip_confirmation=True  → returns True immediately

 E. _confirm_destroy  — user answers y           → returns TrueConfirmation1.  destroy --include solution  → local file kept,  K8s secret kept

 F. _confirm_destroy  — user answers n           → returns False

 A. User confirms (y)         → destroy proceeds normally2.  destroy --include workspace → local file kept,  K8s secret kept

_all_resources_cleared

 G. all IDs empty            → True B. User refuses (n / Enter)  → destroy cancelled, nothing modified3.  destroy complet réussi      → local file deleted, K8s secret deleted

 H. one ID still set         → False

 C. --include message         → scope mentions specific resource4.  destroy complet, remote=False → local file deleted, K8s never touched

destroy command — confirmation gate

 I. user refuses             → nothing modified, success returned D. --exclude message         → scope mentions exclusion5.  Secret K8s déjà absent      → pas d'erreur bloquante

 J. --yes skips confirmation → destroy proceeds

 E. no flags message          → scope mentions ALL resources6.  Fichier local déjà absent   → pas d'erreur bloquante

State cleanup

 1.  destroy --include solution  → local file kept,  K8s secret kept7.  Ordre garanti               → store/delete local avant delete K8s

 2.  destroy --include workspace → local file kept,  K8s secret kept

 3.  destroy complet réussi      → local file deleted, K8s secret deletedState cleanup8.  IDs résiduels               → state local conservé même sans --include

 4.  destroy complet, remote=False → local file deleted, K8s never touched

 5.  Secret K8s déjà absent      → pas d'erreur bloquante 1.  destroy --include solution  → local file kept,  K8s secret kept"""

 6.  Fichier local déjà absent   → pas d'erreur bloquante

 7.  Ordre garanti               → delete local avant delete K8s 2.  destroy --include workspace → local file kept,  K8s secret kept

 8.  IDs résiduels               → states conservés même sans --include

""" 3.  destroy complet réussi      → local file deleted, K8s secret deletedfrom unittest.mock import MagicMock, patch



from unittest.mock import MagicMock, patch 4.  destroy complet, remote=False → local file deleted, K8s never touched



import pytest 5.  Secret K8s déjà absent      → pas d'erreur bloquante



 6.  Fichier local déjà absent   → pas d'erreur bloquante# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------

# Helpers 7.  Ordre garanti               → delete local avant delete K8s# Helpers

# ---------------------------------------------------------------------------

 8.  IDs résiduels               → states conservés même sans --include# ---------------------------------------------------------------------------

def _make_state(remote: bool = True, **overrides) -> dict:

    return {"""

        "context": "ctx",

        "tenant": "tenant",def _make_state(remote: bool = True, **overrides) -> dict:

        "remote": remote,

        "services": {from unittest.mock import MagicMock, call, patch    return {

            "api": {

                "organization_id": overrides.get("organization_id", ""),        "context": "ctx",

                "solution_id": overrides.get("solution_id", ""),

                "workspace_id": overrides.get("workspace_id", ""),import pytest        "tenant": "tenant",

            },

            "webapp": {"webapp_name": overrides.get("webapp_name", ""), "webapp_url": ""},        "remote": remote,

            "postgres": {"schema_name": overrides.get("schema_name", "")},

        },        "services": {

    }

# ---------------------------------------------------------------------------            "api": {



def _run_destroy(state: dict, include: tuple = (), exclude: tuple = (), skip_confirmation: bool = True):# Helpers                "organization_id": overrides.get("organization_id", ""),

    """Invoke the raw destroy callback. Skips confirmation by default."""

    from Babylon.commands.macro.destroy import destroy as _cmd# ---------------------------------------------------------------------------                "solution_id": overrides.get("solution_id", ""),



    _cmd.callback(state=state, include=include, exclude=exclude, skip_confirmation=skip_confirmation)                "workspace_id": overrides.get("workspace_id", ""),



def _make_state(remote: bool = True, **overrides) -> dict:            },

def _mock_env():

    m = MagicMock()    return {            "webapp": {"webapp_name": overrides.get("webapp_name", ""), "webapp_url": ""},

    m.environ_id = "tenant"

    m.delete_state_in_local.return_value = True        "context": "ctx",            "postgres": {"schema_name": overrides.get("schema_name", "")},

    m.delete_state_in_kubernetes.return_value = True

    return m        "tenant": "tenant",        },



        "remote": remote,    }

# ---------------------------------------------------------------------------

# A–C  _get_destroy_scope        "services": {

# ---------------------------------------------------------------------------

            "api": {

class TestGetDestroyScope:

                "organization_id": overrides.get("organization_id", ""),def _run_destroy(state: dict):

    def test_no_flags_returns_all_resources(self):

        from Babylon.commands.macro.destroy import _get_destroy_scope                "solution_id": overrides.get("solution_id", ""),    from Babylon.commands.macro.destroy import destroy as _cmd

        assert _get_destroy_scope((), ()) == "all resources"

                "workspace_id": overrides.get("workspace_id", ""),    _cmd.callback(state=state, include=(), exclude=())

    def test_include_lists_resources(self):

        from Babylon.commands.macro.destroy import _get_destroy_scope            },

        assert _get_destroy_scope(("solution", "workspace"), ()) == "resources: solution, workspace"

            "webapp": {"webapp_name": overrides.get("webapp_name", ""), "webapp_url": ""},

    def test_exclude_lists_exceptions(self):

        from Babylon.commands.macro.destroy import _get_destroy_scope            "postgres": {"schema_name": overrides.get("schema_name", "")},def _mock_env():

        assert _get_destroy_scope((), ("webapp",)) == "all resources except: webapp"

        },    m = MagicMock()



# ---------------------------------------------------------------------------    }    m.environ_id = "tenant"

# D–F  _confirm_destroy

# ---------------------------------------------------------------------------    m.delete_state_in_local.return_value = True



class TestConfirmDestroy:    m.delete_state_in_kubernetes.return_value = True



    def test_skip_confirmation_returns_true(self):def _run_destroy(state: dict, include: tuple = (), exclude: tuple = (), confirm_answer: bool = True):    return m

        from Babylon.commands.macro.destroy import _confirm_destroy

        with patch("Babylon.commands.macro.destroy.env") as mock_env:    """Invoke the raw destroy callback, auto-answering the interactive prompt."""

            mock_env.environ_id = "tenant"

            result = _confirm_destroy(include=(), exclude=(), skip_confirmation=True)    from Babylon.commands.macro.destroy import destroy as _cmd

        assert result is True

# ---------------------------------------------------------------------------

    def test_user_confirms_returns_true(self):

        from Babylon.commands.macro.destroy import _confirm_destroy    with patch("Babylon.commands.macro.destroy.confirm", return_value=confirm_answer):# Tests

        with (

            patch("Babylon.commands.macro.destroy.env") as mock_env,        _cmd.callback(state=state, include=include, exclude=exclude)# ---------------------------------------------------------------------------

            patch("Babylon.commands.macro.destroy.confirm", return_value=True),

        ):

            mock_env.environ_id = "tenant"

            result = _confirm_destroy(include=(), exclude=(), skip_confirmation=False)class TestDestroyStateCleanup:

        assert result is True

def _mock_env():

    def test_user_refuses_returns_false(self):

        from Babylon.commands.macro.destroy import _confirm_destroy    m = MagicMock()    # ── 1. partial — solution only ───────────────────────────────────────────

        with (

            patch("Babylon.commands.macro.destroy.env") as mock_env,    m.environ_id = "tenant"

            patch("Babylon.commands.macro.destroy.confirm", return_value=False),

        ):    m.delete_state_in_local.return_value = True    def test_partial_solution_keeps_both_states(self):

            mock_env.environ_id = "tenant"

            result = _confirm_destroy(include=(), exclude=(), skip_confirmation=False)    m.delete_state_in_kubernetes.return_value = True        mock_env = _mock_env()

        assert result is False

    return m        state = _make_state(remote=True, organization_id="o-1", workspace_id="w-1")



# ---------------------------------------------------------------------------

# G–H  _all_resources_cleared

# ---------------------------------------------------------------------------        with (



class TestAllResourcesCleared:# ---------------------------------------------------------------------------            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(False, True, False, False)),



    def test_all_empty_returns_true(self):# A–E  Interactive confirmation            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),

        from Babylon.commands.macro.destroy import _all_resources_cleared

        assert _all_resources_cleared(_make_state()) is True# ---------------------------------------------------------------------------            patch("Babylon.commands.macro.destroy.env", mock_env),



    def test_one_id_set_returns_false(self):        ):

        from Babylon.commands.macro.destroy import _all_resources_cleared

        assert _all_resources_cleared(_make_state(organization_id="o-1")) is Falseclass TestDestroyConfirmation:            _run_destroy(state)



    def test_webapp_set_returns_false(self):

        from Babylon.commands.macro.destroy import _all_resources_cleared

        assert _all_resources_cleared(_make_state(webapp_name="app")) is False    # ── A. user confirms → destroy proceeds ──────────────────────────────────        mock_env.delete_state_in_local.assert_not_called()



    def test_schema_set_returns_false(self):        mock_env.store_state_in_local.assert_called_once_with(state=state)

        from Babylon.commands.macro.destroy import _all_resources_cleared

        assert _all_resources_cleared(_make_state(schema_name="schema")) is False    def test_confirm_yes_proceeds(self):        mock_env.delete_state_in_kubernetes.assert_not_called()



        mock_env = _mock_env()        mock_env.store_state_in_kubernetes.assert_called_once_with(state=state)

# ---------------------------------------------------------------------------

# I–J  destroy command — confirmation gate        state = _make_state(remote=False)

# ---------------------------------------------------------------------------

    # ── 2. partial — workspace only ──────────────────────────────────────────

class TestDestroyConfirmationGate:

        with (

    def test_user_refuses_nothing_modified(self):

        mock_env = _mock_env()            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(True, True, True, True)),    def test_partial_workspace_keeps_both_states(self):

        state = _make_state(remote=True, organization_id="o-1")

            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),        mock_env = _mock_env()

        with (

            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(True, True, True, True)),            patch("Babylon.commands.macro.destroy.env", mock_env),        state = _make_state(remote=True, organization_id="o-1", solution_id="s-1")

            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),

            patch("Babylon.commands.macro.destroy.env", mock_env),        ):

            patch("Babylon.commands.macro.destroy.confirm", return_value=False),

        ):            _run_destroy(state, confirm_answer=True)        with (

            _run_destroy(state, skip_confirmation=False)

            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(False, False, True, False)),

        mock_env.store_state_in_local.assert_not_called()

        mock_env.delete_state_in_local.assert_not_called()        # At least local cleanup should have been triggered            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),

        mock_env.store_state_in_kubernetes.assert_not_called()

        mock_env.delete_state_in_kubernetes.assert_not_called()        mock_env.delete_state_in_local.assert_called_once()            patch("Babylon.commands.macro.destroy.env", mock_env),



    def test_yes_flag_skips_confirm_and_proceeds(self):        ):

        mock_env = _mock_env()

        state = _make_state(remote=False)    # ── B. user refuses → nothing is touched ─────────────────────────────────            _run_destroy(state)



        with (

            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(True, True, True, True)),

            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),    def test_confirm_no_cancels_destroy(self):        mock_env.delete_state_in_local.assert_not_called()

            patch("Babylon.commands.macro.destroy.env", mock_env),

            patch("Babylon.commands.macro.destroy.confirm") as mock_confirm,        mock_env = _mock_env()        mock_env.store_state_in_local.assert_called_once_with(state=state)

        ):

            _run_destroy(state, skip_confirmation=True)        state = _make_state(remote=True, organization_id="o-1", solution_id="s-1")        mock_env.delete_state_in_kubernetes.assert_not_called()



        mock_confirm.assert_not_called()        mock_env.store_state_in_kubernetes.assert_called_once_with(state=state)

        mock_env.delete_state_in_local.assert_called_once()

        with (



# ---------------------------------------------------------------------------            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(True, True, True, True)),    # ── 3. full destroy, remote=True → both deleted ──────────────────────────

# 1–8  State cleanup

# ---------------------------------------------------------------------------            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),



class TestDestroyStateCleanup:            patch("Babylon.commands.macro.destroy.env", mock_env),    def test_full_destroy_remote_true_deletes_both(self):



    # ── 1. partial — solution only ───────────────────────────────────────────        ):        mock_env = _mock_env()



    def test_partial_solution_keeps_both_states(self):            _run_destroy(state, confirm_answer=False)        state = _make_state(remote=True)  # all IDs already ""

        mock_env = _mock_env()

        state = _make_state(remote=True, organization_id="o-1", workspace_id="w-1")



        with (        # No state write or delete must happen        with (

            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(False, True, False, False)),

            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),        mock_env.store_state_in_local.assert_not_called()            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(True, True, True, True)),

            patch("Babylon.commands.macro.destroy.env", mock_env),

        ):        mock_env.delete_state_in_local.assert_not_called()            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),

            _run_destroy(state)

        mock_env.store_state_in_kubernetes.assert_not_called()            patch("Babylon.commands.macro.destroy.env", mock_env),

        mock_env.delete_state_in_local.assert_not_called()

        mock_env.store_state_in_local.assert_called_once_with(state=state)        mock_env.delete_state_in_kubernetes.assert_not_called()        ):

        mock_env.delete_state_in_kubernetes.assert_not_called()

        mock_env.store_state_in_kubernetes.assert_called_once_with(state=state)            _run_destroy(state)



    # ── 2. partial — workspace only ──────────────────────────────────────────    # ── C. --include: confirm prompt is called (message adapted) ─────────────



    def test_partial_workspace_keeps_both_states(self):        mock_env.delete_state_in_local.assert_called_once()

        mock_env = _mock_env()

        state = _make_state(remote=True, organization_id="o-1", solution_id="s-1")    def test_confirm_called_with_include(self):        mock_env.store_state_in_local.assert_not_called()



        with (        mock_env = _mock_env()        mock_env.delete_state_in_kubernetes.assert_called_once()

            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(False, False, True, False)),

            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),        state = _make_state(remote=False)        mock_env.store_state_in_kubernetes.assert_not_called()

            patch("Babylon.commands.macro.destroy.env", mock_env),

        ):

            _run_destroy(state)

        with (    # ── 4. full destroy, remote=False → local deleted, K8s untouched ─────────

        mock_env.delete_state_in_local.assert_not_called()

        mock_env.store_state_in_local.assert_called_once_with(state=state)            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(False, True, False, False)),

        mock_env.delete_state_in_kubernetes.assert_not_called()

        mock_env.store_state_in_kubernetes.assert_called_once_with(state=state)            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),    def test_full_destroy_remote_false_deletes_only_local(self):



    # ── 3. full destroy, remote=True → both deleted ──────────────────────────            patch("Babylon.commands.macro.destroy.env", mock_env),        mock_env = _mock_env()



    def test_full_destroy_remote_true_deletes_both(self):            patch("Babylon.commands.macro.destroy.confirm", return_value=False) as mock_confirm,        state = _make_state(remote=False)

        mock_env = _mock_env()

        state = _make_state(remote=True)        ):



        with (            from Babylon.commands.macro.destroy import destroy as _cmd        with (

            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(True, True, True, True)),

            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),            _cmd.callback(state=state, include=("solution",), exclude=())            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(True, True, True, True)),

            patch("Babylon.commands.macro.destroy.env", mock_env),

        ):            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),

            _run_destroy(state)

        mock_confirm.assert_called_once()            patch("Babylon.commands.macro.destroy.env", mock_env),

        mock_env.delete_state_in_local.assert_called_once()

        mock_env.store_state_in_local.assert_not_called()        ):

        mock_env.delete_state_in_kubernetes.assert_called_once()

        mock_env.store_state_in_kubernetes.assert_not_called()    # ── D. --exclude: confirm prompt is called ────────────────────────────────            _run_destroy(state)



    # ── 4. full destroy, remote=False → local deleted, K8s untouched ─────────



    def test_full_destroy_remote_false_deletes_only_local(self):    def test_confirm_called_with_exclude(self):        mock_env.delete_state_in_local.assert_called_once()

        mock_env = _mock_env()

        state = _make_state(remote=False)        mock_env = _mock_env()        mock_env.store_state_in_local.assert_not_called()



        with (        state = _make_state(remote=False)        mock_env.delete_state_in_kubernetes.assert_not_called()

            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(True, True, True, True)),

            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),        mock_env.store_state_in_kubernetes.assert_not_called()

            patch("Babylon.commands.macro.destroy.env", mock_env),

        ):        with (

            _run_destroy(state)

            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(True, False, True, True)),    # ── 5. K8s secret already absent → not a blocking error ──────────────────

        mock_env.delete_state_in_local.assert_called_once()

        mock_env.store_state_in_local.assert_not_called()            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),

        mock_env.delete_state_in_kubernetes.assert_not_called()

        mock_env.store_state_in_kubernetes.assert_not_called()            patch("Babylon.commands.macro.destroy.env", mock_env),    def test_k8s_secret_already_absent_not_blocking(self):



    # ── 5. K8s secret already absent → not a blocking error ──────────────────            patch("Babylon.commands.macro.destroy.confirm", return_value=False) as mock_confirm,        mock_env = _mock_env()



    def test_k8s_secret_already_absent_not_blocking(self):        ):        mock_env.delete_state_in_kubernetes.return_value = True  # 404 path

        mock_env = _mock_env()

        mock_env.delete_state_in_kubernetes.return_value = True            from Babylon.commands.macro.destroy import destroy as _cmd        state = _make_state(remote=True)

        state = _make_state(remote=True)

            _cmd.callback(state=state, include=(), exclude=("solution",))

        with (

            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(True, True, True, True)),        with (

            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),

            patch("Babylon.commands.macro.destroy.env", mock_env),        mock_confirm.assert_called_once()            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(True, True, True, True)),

        ):

            _run_destroy(state)            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),



        mock_env.delete_state_in_kubernetes.assert_called_once()    # ── E. no flags: confirm prompt is called ────────────────────────────────            patch("Babylon.commands.macro.destroy.env", mock_env),



    # ── 6. local file already absent → not a blocking error ──────────────────        ):



    def test_local_file_already_absent_not_blocking(self):    def test_confirm_called_with_no_flags(self):            _run_destroy(state)  # must not raise

        mock_env = _mock_env()

        mock_env.delete_state_in_local.return_value = True        mock_env = _mock_env()

        state = _make_state(remote=False)

        state = _make_state(remote=False)        mock_env.delete_state_in_kubernetes.assert_called_once()

        with (

            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(True, True, True, True)),

            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),

            patch("Babylon.commands.macro.destroy.env", mock_env),        with (    # ── 6. local file already absent → not a blocking error ──────────────────

        ):

            _run_destroy(state)            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(True, True, True, True)),



        mock_env.delete_state_in_local.assert_called_once()            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),    def test_local_file_already_absent_not_blocking(self):



    # ── 7. order: local cleanup before K8s ───────────────────────────────────            patch("Babylon.commands.macro.destroy.env", mock_env),        mock_env = _mock_env()



    def test_local_cleanup_before_kubernetes_cleanup(self):            patch("Babylon.commands.macro.destroy.confirm", return_value=False) as mock_confirm,        mock_env.delete_state_in_local.return_value = True  # already gone

        mock_env = _mock_env()

        call_order: list[str] = []        ):        state = _make_state(remote=False)

        mock_env.delete_state_in_local.side_effect = lambda: call_order.append("delete_local") or True

        mock_env.delete_state_in_kubernetes.side_effect = lambda: call_order.append("delete_k8s") or True            from Babylon.commands.macro.destroy import destroy as _cmd

        state = _make_state(remote=True)

            _cmd.callback(state=state, include=(), exclude=())        with (

        with (

            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(True, True, True, True)),            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(True, True, True, True)),

            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),

            patch("Babylon.commands.macro.destroy.env", mock_env),        mock_confirm.assert_called_once()            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),

        ):

            _run_destroy(state)            patch("Babylon.commands.macro.destroy.env", mock_env),



        assert "delete_local" in call_order and "delete_k8s" in call_order    # ── Confirm must be called BEFORE any destructive operation ──────────────        ):

        assert call_order.index("delete_local") < call_order.index("delete_k8s")

            _run_destroy(state)  # must not raise

    # ── 8. any residual ID keeps both states ─────────────────────────────────

    def test_confirm_before_any_destructive_call(self):

    def test_any_remaining_id_keeps_both_states(self):

        mock_env = _mock_env()        mock_env = _mock_env()        mock_env.delete_state_in_local.assert_called_once()

        state = _make_state(remote=True, organization_id="o-999")

        call_order: list[str] = []

        with (

            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(False, False, False, True)),    # ── 7. order: local cleanup always before K8s cleanup ────────────────────

            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),

            patch("Babylon.commands.macro.destroy.env", mock_env),        mock_env.delete_state_in_local.side_effect = lambda: call_order.append("delete_local") or True

        ):

            _run_destroy(state)        mock_env.store_state_in_local.side_effect = lambda **_: call_order.append("store_local")    def test_local_cleanup_before_kubernetes_cleanup(self):



        mock_env.delete_state_in_local.assert_not_called()        mock_env = _mock_env()

        mock_env.store_state_in_local.assert_called_once_with(state=state)

        mock_env.delete_state_in_kubernetes.assert_not_called()        state = _make_state(remote=False)        call_order: list[str] = []

        mock_env.store_state_in_kubernetes.assert_called_once_with(state=state)

        mock_env.delete_state_in_local.side_effect = lambda: call_order.append("delete_local") or True

        def _confirm_side_effect(*args, **kwargs):        mock_env.delete_state_in_kubernetes.side_effect = lambda: call_order.append("delete_k8s") or True

            call_order.append("confirm")        state = _make_state(remote=True)

            return True

        with (

        with (            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(True, True, True, True)),

            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(True, True, True, True)),            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),

            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),            patch("Babylon.commands.macro.destroy.env", mock_env),

            patch("Babylon.commands.macro.destroy.env", mock_env),        ):

            patch("Babylon.commands.macro.destroy.confirm", side_effect=_confirm_side_effect),            _run_destroy(state)

        ):

            from Babylon.commands.macro.destroy import destroy as _cmd        assert "delete_local" in call_order and "delete_k8s" in call_order

            _cmd.callback(state=state, include=(), exclude=())        assert call_order.index("delete_local") < call_order.index("delete_k8s")



        first_destructive = next(    # ── 8. any residual ID keeps both states ─────────────────────────────────

            (i for i, v in enumerate(call_order) if v in ("delete_local", "store_local")),

            None,    def test_any_remaining_id_keeps_both_states(self):

        )        mock_env = _mock_env()

        confirm_index = call_order.index("confirm")        # Only the webapp was destroyed but org still exists

        assert first_destructive is not None        state = _make_state(remote=True, organization_id="o-999")

        assert confirm_index < first_destructive, (

            "confirm() must be called before any destructive operation"        with (

        )            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(False, False, False, True)),

            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),

            patch("Babylon.commands.macro.destroy.env", mock_env),

# ---------------------------------------------------------------------------        ):

# 1–8  State cleanup (confirm auto-answered True)            _run_destroy(state)

# ---------------------------------------------------------------------------

        mock_env.delete_state_in_local.assert_not_called()

class TestDestroyStateCleanup:        mock_env.store_state_in_local.assert_called_once_with(state=state)

        mock_env.delete_state_in_kubernetes.assert_not_called()

    # ── 1. partial — solution only ───────────────────────────────────────────        mock_env.store_state_in_kubernetes.assert_called_once_with(state=state)


    def test_partial_solution_keeps_both_states(self):
        mock_env = _mock_env()
        state = _make_state(remote=True, organization_id="o-1", workspace_id="w-1")

        with (
            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(False, True, False, False)),
            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),
            patch("Babylon.commands.macro.destroy.env", mock_env),
        ):
            _run_destroy(state)

        mock_env.delete_state_in_local.assert_not_called()
        mock_env.store_state_in_local.assert_called_once_with(state=state)
        mock_env.delete_state_in_kubernetes.assert_not_called()
        mock_env.store_state_in_kubernetes.assert_called_once_with(state=state)

    # ── 2. partial — workspace only ──────────────────────────────────────────

    def test_partial_workspace_keeps_both_states(self):
        mock_env = _mock_env()
        state = _make_state(remote=True, organization_id="o-1", solution_id="s-1")

        with (
            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(False, False, True, False)),
            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),
            patch("Babylon.commands.macro.destroy.env", mock_env),
        ):
            _run_destroy(state)

        mock_env.delete_state_in_local.assert_not_called()
        mock_env.store_state_in_local.assert_called_once_with(state=state)
        mock_env.delete_state_in_kubernetes.assert_not_called()
        mock_env.store_state_in_kubernetes.assert_called_once_with(state=state)

    # ── 3. full destroy, remote=True → both deleted ──────────────────────────

    def test_full_destroy_remote_true_deletes_both(self):
        mock_env = _mock_env()
        state = _make_state(remote=True)

        with (
            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(True, True, True, True)),
            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),
            patch("Babylon.commands.macro.destroy.env", mock_env),
        ):
            _run_destroy(state)

        mock_env.delete_state_in_local.assert_called_once()
        mock_env.store_state_in_local.assert_not_called()
        mock_env.delete_state_in_kubernetes.assert_called_once()
        mock_env.store_state_in_kubernetes.assert_not_called()

    # ── 4. full destroy, remote=False → local deleted, K8s untouched ─────────

    def test_full_destroy_remote_false_deletes_only_local(self):
        mock_env = _mock_env()
        state = _make_state(remote=False)

        with (
            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(True, True, True, True)),
            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),
            patch("Babylon.commands.macro.destroy.env", mock_env),
        ):
            _run_destroy(state)

        mock_env.delete_state_in_local.assert_called_once()
        mock_env.store_state_in_local.assert_not_called()
        mock_env.delete_state_in_kubernetes.assert_not_called()
        mock_env.store_state_in_kubernetes.assert_not_called()

    # ── 5. K8s secret already absent → not a blocking error ──────────────────

    def test_k8s_secret_already_absent_not_blocking(self):
        mock_env = _mock_env()
        mock_env.delete_state_in_kubernetes.return_value = True
        state = _make_state(remote=True)

        with (
            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(True, True, True, True)),
            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),
            patch("Babylon.commands.macro.destroy.env", mock_env),
        ):
            _run_destroy(state)

        mock_env.delete_state_in_kubernetes.assert_called_once()

    # ── 6. local file already absent → not a blocking error ──────────────────

    def test_local_file_already_absent_not_blocking(self):
        mock_env = _mock_env()
        mock_env.delete_state_in_local.return_value = True
        state = _make_state(remote=False)

        with (
            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(True, True, True, True)),
            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),
            patch("Babylon.commands.macro.destroy.env", mock_env),
        ):
            _run_destroy(state)

        mock_env.delete_state_in_local.assert_called_once()

    # ── 7. order: local cleanup before K8s ───────────────────────────────────

    def test_local_cleanup_before_kubernetes_cleanup(self):
        mock_env = _mock_env()
        call_order: list[str] = []
        mock_env.delete_state_in_local.side_effect = lambda: call_order.append("delete_local") or True
        mock_env.delete_state_in_kubernetes.side_effect = lambda: call_order.append("delete_k8s") or True
        state = _make_state(remote=True)

        with (
            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(True, True, True, True)),
            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),
            patch("Babylon.commands.macro.destroy.env", mock_env),
        ):
            _run_destroy(state)

        assert "delete_local" in call_order and "delete_k8s" in call_order
        assert call_order.index("delete_local") < call_order.index("delete_k8s")

    # ── 8. any residual ID keeps both states ─────────────────────────────────

    def test_any_remaining_id_keeps_both_states(self):
        mock_env = _mock_env()
        state = _make_state(remote=True, organization_id="o-999")

        with (
            patch("Babylon.commands.macro.destroy.resolve_inclusion_exclusion", return_value=(False, False, False, True)),
            patch("Babylon.commands.macro.destroy.get_keycloak_token", return_value=("token", {})),
            patch("Babylon.commands.macro.destroy.env", mock_env),
        ):
            _run_destroy(state)

        mock_env.delete_state_in_local.assert_not_called()
        mock_env.store_state_in_local.assert_called_once_with(state=state)
        mock_env.delete_state_in_kubernetes.assert_not_called()
        mock_env.store_state_in_kubernetes.assert_called_once_with(state=state)
