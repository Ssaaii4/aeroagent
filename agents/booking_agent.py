import asyncio
from playwright.async_api import async_playwright
from tools.keyvault_tool import get_secret
from config import DEMO_MODE

async def fill_booking_form(flight: dict, passenger: dict) -> dict:
    if DEMO_MODE:
        return {
            "airline":    flight.get("airline", "Demo Air"),
            "flight_no":  flight.get("flight_no", "DA100"),
            "departs":    flight.get("departure", "08:00"),
            "arrives":    flight.get("arrival",   "20:00"),
            "seat":       "14C (aisle)",
            "total":      f"${flight.get('price_usd', 0):.2f}",
            "page_state": {"demo": True}
        }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page    = await browser.new_page()
        await page.goto(flight.get("booking_url", ""), timeout=30000)
        await page.fill('[name="firstName"]', passenger["first"])
        await page.fill('[name="lastName"]',  passenger["last"])
        await page.fill('[name="passport"]',  passenger["passport"])
        await page.fill('[name="email"]',     passenger["email"])
        await page.click('[data-action="continue-to-review"]')
        await page.wait_for_selector('#booking-summary', timeout=15000)
        summary = {
            "airline":    flight["airline"],
            "flight_no":  await _text(page, '#flight-number'),
            "departs":    await _text(page, '#depart-time'),
            "arrives":    await _text(page, '#arrive-time'),
            "seat":       await _text(page, '#assigned-seat'),
            "total":      await _text(page, '#total-price'),
            "page_state": await page.context.storage_state()
        }
        await browser.close()
        return summary

async def complete_payment(page_state: dict, passenger: dict) -> dict:
    if DEMO_MODE or page_state.get("demo"):
        return {
            "pnr":     "DEMO-PNR-2026",
            "charged": page_state.get("total", "$0.00"),
            "status":  "confirmed (sandbox)"
        }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx     = await browser.new_context(storage_state=page_state)
        page    = await ctx.new_page()
        await page.fill('#card-number', get_secret("card-number"))
        await page.fill('#card-expiry', get_secret("card-expiry"))
        await page.fill('#card-cvv',    get_secret("card-cvv"))
        await page.click('#pay-now-btn')
        await page.wait_for_selector('#booking-confirmed', timeout=20000)
        pnr   = await page.locator('#pnr-code').text_content()
        price = await page.locator('#charged-amount').text_content()
        await browser.close()
        return {"pnr": pnr, "charged": price, "status": "confirmed"}

async def _text(page, sel):
    el = page.locator(sel)
    return await el.text_content() if await el.count() else "n/a"