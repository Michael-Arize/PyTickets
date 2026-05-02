# Adding a New Ticket Site

PyTickets supports new sites through a small adapter plus a JSON config. The rest
of the system, including filtering, deduplication, email notifications,
scheduling, the API, dashboard, and database, works automatically once the site
is registered.

## 1. Create a Site Config

Add `configs/sites/example_site.json`:

```json
{
  "name": "Example Site",
  "base_url": "https://example.com",
  "auth": {
    "type": "none",
    "credentials": {}
  },
  "selectors": {
    "ticket_array_xpath": "//a[contains(@href, '/tickets/')]",
    "ticket_link_xpath": "./@href",
    "no_tickets_text": ["sold out", "no tickets available"],
    "rate_limit_text": ["too many requests", "access denied"]
  },
  "proxy_required": false,
  "rate_limit": {
    "min_delay": 2.0,
    "max_delay": 5.0
  }
}
```

Use `env:NAME` for required environment variables and
`env_optional:NAME` for optional ones.

## 2. Create an Adapter

Add `ticketCrawler/adapters/site_adapters/example_site.py`.

At minimum, implement the abstract methods from `BaseAdapter`. For the current
manual-purchase workflow, `buy_ticket()` and `check_reservation_success()` should
return `False`; PyTickets sends links and never checks out automatically.

The adapter can return either Scrapy selectors or dictionaries from
`extract_tickets()`. Dictionaries should use these keys when possible:

```python
{
    "url": "https://example.com/tickets/123",
    "price": 25.0,
    "seat_type": "Floor",
    "date": "2026-05-02T20:00:00",
    "quantity": 2,
    "metadata": {"source": "json_ld"}
}
```

If a site has an official discovery API, prefer parsing that JSON response in the
adapter and returning the event/ticket URL for manual purchase. Ticketmaster and
SeatGeek both follow this pattern while still supporting HTML fallback parsing.

## 3. Register the Adapter

Update `ticketCrawler/adapters/factory.py`:

```python
from .site_adapters.example_site import ExampleSiteAdapter

ADAPTERS = {
    "example_site": ExampleSiteAdapter,
}
```

## 4. Add Tests

Add coverage in `tests/test_adapters.py`:

- the adapter appears in `AdapterFactory.list_adapters()`
- the adapter can be created
- representative HTML/JSON produces the expected ticket URL

## 5. Run It

```bash
python -m pytest
scrapy crawl tickets_refactored -a site=example_site -a url=https://example.com/search
```

For recurring runs, use the dashboard at `http://localhost:8000` or
`run_scheduler.py`.
