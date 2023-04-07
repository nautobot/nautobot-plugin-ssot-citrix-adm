"""Nautobot SSoT Citrix ADM Adapter for Citrix ADM SSoT plugin."""

from diffsync import DiffSync


class CitrixAdmAdapter(DiffSync):
    """DiffSync adapter for Citrix ADM."""

    top_level = []

    def __init__(self, *args, job=None, sync=None, client=None, **kwargs):
        """Initialize Citrix ADM.

        Args:
            job (object, optional): Citrix ADM job. Defaults to None.
            sync (object, optional): Citrix ADM DiffSync. Defaults to None.
            client (object): Citrix ADM API client connection object.
        """
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync
        self.conn = client

    def load(self):
        """Load data from Citrix ADM into DiffSync models."""
        raise NotImplementedError
