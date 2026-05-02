# -*- coding: utf-8 -*-
"""Run the PyTickets API and dashboard."""
import os

import uvicorn


if __name__ == "__main__":
    uvicorn.run(
        "ticketCrawler.api.app:app",
        host=os.environ.get("PYTICKETS_API_HOST", "0.0.0.0"),
        port=int(os.environ.get("PYTICKETS_API_PORT", "8000")),
        reload=False,
    )
