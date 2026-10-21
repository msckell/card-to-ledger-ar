"""Synthetic September 2026 for Andes Labs SRL (fictional), with ground truth.

One seeded command writes:
- data/raw/transactions.json   the card and account export (assumed export format)
- data/raw/receipts/RC-*.pdf   receipts and contractor invoices, not linked to transactions
- data/truth/ground_truth.json the correct answer for every transaction and receipt

Every amount is synthetic. Exchange rates come from the cited snapshot in data/fx/.
"""

from __future__ import annotations

import random
import shutil
from dataclasses import dataclass, field
from datetime import date, timedelta

from pipeline import fx
from pipeline.jsonio import write_json
from pipeline.money import cents_str, convert, to_cents
from pipeline.paths import RAW, RECEIPTS, TRUTH
from pipeline.receipts_pdf import render

SEED = 20260930
YEAR, MONTH = 2026, 9

CARDHOLDERS = [
    ("Sofía Paz", "4821"),
    ("Martín Ibarra", "1907"),
    ("Lucía Fernández", "3365"),
    ("Diego Romero", "5402"),
    ("Valentina Sosa", "7718"),
    ("Julián Castro", "2290"),
    ("Camila Ortiz", "6043"),
    ("Tomás Herrera", "8156"),
]


@dataclass
class Merchant:
    key: str
    descriptor: str  # `{r}` becomes a random reference
    vendor: str
    address: str
    account: str
    layout: str  # saas | es | pos | flight | hotel
    count: int
    lo: int  # whole dollars
    hi: int
    items: list[str]
    days: list[int] | None = None
    ambiguous: bool = False
    memo: str = ""
    tip: bool = False


# Merchants covered by rules in config/rules.yaml. Uber Eats is caught by the broad Uber rule
# on purpose: rules can be wrong too, and the eval measures it.
COVERED = [
    Merchant(
        "meta",
        "FACEBK *ADS {r}",
        "Meta Platforms Ireland Ltd",
        "4 Grand Canal Square, Dublin 2, Ireland",
        "5.1.01",
        "saas",
        12,
        150,
        1400,
        ["Meta ads, campaign spend"],
    ),
    Merchant(
        "gads",
        "GOOGLE *ADS{r}",
        "Google Ireland Ltd",
        "Gordon House, Barrow Street, Dublin 4, Ireland",
        "5.1.01",
        "saas",
        9,
        120,
        1100,
        ["Google Ads, search campaigns"],
    ),
    Merchant(
        "linkedin",
        "LINKEDIN *ADS {r}",
        "LinkedIn Ireland Unlimited Company",
        "Wilton Plaza, Dublin 2, Ireland",
        "5.1.01",
        "saas",
        3,
        300,
        900,
        ["LinkedIn Campaign Manager, sponsored content"],
    ),
    Merchant(
        "aws",
        "AWS EMEA",
        "Amazon Web Services EMEA SARL",
        "38 Avenue John F. Kennedy, L-1855 Luxembourg",
        "5.1.02",
        "saas",
        2,
        1800,
        4200,
        ["AWS usage, August 2026", "AWS Marketplace subscription"],
        days=[2, 3],
    ),
    Merchant(
        "gcp",
        "GOOGLE *CLOUD {r}",
        "Google Cloud EMEA Limited",
        "70 Sir John Rogerson's Quay, Dublin 2, Ireland",
        "5.1.02",
        "saas",
        1,
        600,
        1500,
        ["Google Cloud Platform usage, August 2026"],
        days=[2],
    ),
    Merchant(
        "vercel",
        "VERCEL INC.",
        "Vercel Inc.",
        "440 N Barranca Ave, Covina, CA, USA",
        "5.1.02",
        "saas",
        1,
        140,
        400,
        ["Pro plan, team usage"],
        days=[6],
    ),
    Merchant(
        "cloudflare",
        "CLOUDFLARE",
        "Cloudflare, Inc.",
        "101 Townsend St, San Francisco, CA, USA",
        "5.1.02",
        "saas",
        1,
        40,
        250,
        ["Workers paid plan and R2 storage"],
        days=[9],
    ),
    Merchant(
        "datadog",
        "DATADOG INC",
        "Datadog, Inc.",
        "620 8th Ave, New York, NY, USA",
        "5.1.02",
        "saas",
        1,
        500,
        1300,
        ["Infrastructure monitoring, August usage"],
        days=[4],
    ),
    Merchant(
        "workspace",
        "GOOGLE *GSUITE_ANDESLA",
        "Google Workspace",
        "1600 Amphitheatre Pkwy, Mountain View, CA",
        "5.1.03",
        "saas",
        1,
        560,
        620,
        ["Google Workspace Business Standard, 40 users"],
        days=[1],
    ),
    Merchant(
        "slack",
        "SLACK T03AB12",
        "Slack Technologies, LLC",
        "500 Howard St, San Francisco, CA, USA",
        "5.1.03",
        "saas",
        1,
        300,
        360,
        ["Slack Pro, 40 members"],
        days=[3],
    ),
    Merchant(
        "figma",
        "FIGMA",
        "Figma, Inc.",
        "760 Market St, San Francisco, CA, USA",
        "5.1.03",
        "saas",
        2,
        45,
        180,
        ["Figma Professional, editor seats"],
        days=[7, 19],
    ),
    Merchant(
        "notion",
        "NOTION LABS",
        "Notion Labs, Inc.",
        "2300 Harrison St, San Francisco, CA, USA",
        "5.1.03",
        "saas",
        1,
        300,
        420,
        ["Notion Plus, 40 members"],
        days=[5],
    ),
    Merchant(
        "github",
        "GITHUB, INC.",
        "GitHub, Inc.",
        "88 Colin P Kelly Jr St, San Francisco, CA, USA",
        "5.1.03",
        "saas",
        2,
        80,
        420,
        ["GitHub Team, 18 seats", "GitHub Copilot Business"],
        days=[8, 8],
    ),
    Merchant(
        "anthropic",
        "ANTHROPIC",
        "Anthropic, PBC",
        "548 Market St, San Francisco, CA, USA",
        "5.1.03",
        "saas",
        5,
        100,
        900,
        ["API credits"],
    ),
    Merchant(
        "openai",
        "OPENAI *API",
        "OpenAI, LLC",
        "1455 3rd St, San Francisco, CA, USA",
        "5.1.03",
        "saas",
        3,
        50,
        600,
        ["API usage"],
    ),
    Merchant(
        "linear",
        "LINEAR ORBIT",
        "Linear Orbit, Inc.",
        "San Francisco, CA, USA",
        "5.1.03",
        "saas",
        1,
        140,
        200,
        ["Linear Business, 18 seats"],
        days=[10],
    ),
    Merchant(
        "atlassian",
        "ATLASSIAN",
        "Atlassian Pty Ltd",
        "341 George St, Sydney, Australia",
        "5.1.03",
        "saas",
        1,
        90,
        160,
        ["Jira Software Standard"],
        days=[11],
    ),
    Merchant(
        "zoom",
        "ZOOM.COM 888-799-9666",
        "Zoom Communications, Inc.",
        "55 Almaden Blvd, San Jose, CA, USA",
        "5.1.03",
        "saas",
        1,
        60,
        130,
        ["Zoom Workplace Pro, 6 licenses"],
        days=[12],
    ),
    Merchant(
        "onepassword",
        "1PASSWORD",
        "1Password",
        "4711 Yonge St, Toronto, ON, Canada",
        "5.1.03",
        "saas",
        1,
        250,
        320,
        ["1Password Business, 40 users"],
        days=[13],
    ),
    Merchant(
        "loom",
        "LOOM SUBSCRIPTION",
        "Loom, Inc.",
        "140 2nd St, San Francisco, CA, USA",
        "5.1.03",
        "saas",
        1,
        60,
        120,
        ["Loom Business"],
        days=[14],
    ),
    Merchant(
        "miro",
        "MIRO.COM",
        "RealtimeBoard, Inc. (Miro)",
        "201 Spear St, San Francisco, CA, USA",
        "5.1.03",
        "saas",
        1,
        80,
        160,
        ["Miro Starter, 8 members"],
        days=[15],
    ),
    Merchant(
        "hubspot",
        "HUBSPOT INC",
        "HubSpot, Inc.",
        "2 Canal Park, Cambridge, MA, USA",
        "5.1.03",
        "saas",
        1,
        400,
        900,
        ["Sales Hub Professional"],
        days=[16],
    ),
    Merchant(
        "docusign",
        "DOCUSIGN INC",
        "Docusign, Inc.",
        "221 Main St, San Francisco, CA, USA",
        "5.1.03",
        "saas",
        1,
        40,
        90,
        ["Docusign Standard"],
        days=[17],
    ),
    Merchant(
        "canva",
        "CANVA* I04512",
        "Canva Pty Ltd",
        "110 Kippax St, Surry Hills, Australia",
        "5.1.03",
        "saas",
        1,
        100,
        300,
        ["Canva Teams, 5 people"],
        days=[18],
    ),
    Merchant(
        "uber",
        "UBER *TRIP {r}",
        "Uber B.V.",
        "Burgerweeshuispad 301, Amsterdam, Netherlands",
        "5.1.05",
        "saas",
        52,
        7,
        48,
        ["Trip"],
    ),
    Merchant(
        "ubereats",
        "UBER *EATS {r}",
        "Uber Portier B.V.",
        "Burgerweeshuispad 301, Amsterdam, Netherlands",
        "5.1.06",
        "saas",
        4,
        25,
        140,
        ["Food delivery order, team dinner"],
    ),
    Merchant(
        "latam",
        "LATAM AIRLINES {r}",
        "LATAM Airlines Group",
        "Presidente Riesco 5711, Santiago, Chile",
        "5.1.05",
        "es",
        3,
        280,
        900,
        ["Pasaje aéreo EZE-GRU-EZE", "Pasaje aéreo EZE-SCL-EZE"],
    ),
    Merchant(
        "aerolineas",
        "AEROLINEAS ARG {r}",
        "Aerolíneas Argentinas",
        "Av. Rafael Obligado s/n, Buenos Aires",
        "5.1.05",
        "es",
        1,
        300,
        700,
        ["Pasaje aéreo EZE-MIA-EZE"],
    ),
    Merchant(
        "aa",
        "AMERICAN AIR {r}",
        "American Airlines",
        "1 Skyview Dr, Fort Worth, TX, USA",
        "5.1.05",
        "flight",
        2,
        650,
        1400,
        ["Fare", "Taxes and carrier fees"],
    ),
    Merchant(
        "copa",
        "COPA AIR {r}",
        "Copa Airlines",
        "Avenida Principal, Panama City, Panama",
        "5.1.05",
        "flight",
        2,
        400,
        900,
        ["Fare", "Taxes and carrier fees"],
    ),
    Merchant(
        "marriott",
        "MARRIOTT SAO PAULO",
        "Marriott International",
        "Av. Bartolomeu Mitre, Sao Paulo, Brazil",
        "5.1.05",
        "hotel",
        3,
        300,
        900,
        ["Room rate", "Room rate", "Room rate"],
    ),
    Merchant(
        "hilton",
        "HILTON MIAMI DOWNTOWN",
        "Hilton Hotels",
        "1601 Biscayne Blvd, Miami, FL, USA",
        "5.1.05",
        "hotel",
        1,
        400,
        1100,
        ["Room rate", "Room rate"],
    ),
    Merchant(
        "airbnb",
        "AIRBNB * HM{r}",
        "Airbnb Payments",
        "888 Brannan St, San Francisco, CA, USA",
        "5.1.05",
        "saas",
        3,
        250,
        1200,
        ["Stay, 4 nights"],
    ),
    Merchant(
        "booking",
        "BOOKING.COM HOTEL",
        "Booking.com B.V.",
        "Oosterdokskade 163, Amsterdam, Netherlands",
        "5.1.05",
        "saas",
        1,
        200,
        700,
        ["Hotel reservation, 3 nights"],
    ),
    Merchant("toast", "TST* {r}", "", "", "5.1.06", "pos", 31, 18, 160, [], tip=True),
    Merchant(
        "starbucks",
        "STARBUCKS STORE {r}",
        "Starbucks Coffee Company",
        "Starbucks store",
        "5.1.06",
        "pos",
        15,
        5,
        30,
        [],
    ),
    Merchant(
        "eventbrite",
        "EVENTBRITE {r}",
        "Eventbrite",
        "95 Third St, San Francisco, CA, USA",
        "5.1.07",
        "saas",
        3,
        25,
        300,
        ["Event ticket"],
    ),
    Merchant(
        "websummit",
        "WEB SUMMIT RIO",
        "Web Summit",
        "Dublin, Ireland",
        "5.1.07",
        "saas",
        1,
        700,
        1300,
        ["Web Summit Rio, 2 attendee passes"],
        days=[10],
    ),
    Merchant(
        "saastr",
        "SAASTR ANNUAL",
        "SaaStr Inc.",
        "Palo Alto, CA, USA",
        "5.1.07",
        "saas",
        1,
        600,
        1200,
        ["SaaStr Annual, general admission"],
        days=[3],
    ),
    Merchant(
        "udemy",
        "UDEMY ONLINE COURSE",
        "Udemy, Inc.",
        "600 Harrison St, San Francisco, CA, USA",
        "5.1.09",
        "saas",
        2,
        12,
        90,
        ["Online course"],
    ),
    Merchant(
        "coursera",
        "COURSERA",
        "Coursera Inc.",
        "381 E Evelyn Ave, Mountain View, CA, USA",
        "5.1.09",
        "saas",
        1,
        40,
        400,
        ["Coursera Plus, annual"],
    ),
    Merchant(
        "oreilly",
        "OREILLY MEDIA",
        "O'Reilly Media, Inc.",
        "1005 Gravenstein Hwy N, Sebastopol, CA, USA",
        "5.1.09",
        "saas",
        1,
        400,
        500,
        ["O'Reilly learning platform, team"],
    ),
    Merchant(
        "substack",
        "SUBSTACK *{r}",
        "Substack Inc.",
        "111 Sutter St, San Francisco, CA, USA",
        "5.1.09",
        "saas",
        3,
        5,
        20,
        ["Paid newsletter subscription"],
    ),
]

# Merchants with no rule. They go to the AI suggestion step.
AMBIGUOUS = [
    Merchant(
        "bluebottle",
        "SQ *BLUE BOTTLE COFFEE",
        "Blue Bottle Coffee",
        "Mission St, San Francisco, CA, USA",
        "5.1.06",
        "pos",
        2,
        12,
        45,
        [],
        ambiguous=True,
        memo="coffee with a prospect",
    ),
    Merchant(
        "printshop",
        "SQ *SUNSET PRINT SHOP",
        "Sunset Print Shop",
        "Irving St, San Francisco, CA, USA",
        "5.1.08",
        "saas",
        1,
        60,
        160,
        ["Business cards, 500 units, 3 designs"],
        ambiguous=True,
    ),
    Merchant(
        "meetup",
        "SQ *SF DEVS MEETUP",
        "SF Devs Meetup",
        "San Francisco, CA, USA",
        "5.1.07",
        "saas",
        1,
        20,
        60,
        ["Event ticket: AI Infra Night"],
        ambiguous=True,
    ),
    Merchant(
        "mgomez",
        "PAYPAL *MGOMEZSTUDIO",
        "Martina Gómez Studio",
        "Montevideo, Uruguay",
        "5.1.01",
        "es",
        1,
        300,
        700,
        ["Animación de logo para lanzamiento de producto"],
        ambiguous=True,
    ),
    Merchant(
        "screenstudio",
        "PADDLE.NET* SCREENSTUDIO",
        "Screen Studio",
        "Paddle.com Market Ltd, London, UK",
        "5.1.03",
        "saas",
        1,
        89,
        229,
        ["Screen Studio license, 1 year"],
        ambiguous=True,
    ),
    Merchant(
        "tailwind",
        "LEMSQZY* TAILWIND LABS",
        "Tailwind Labs Inc.",
        "Lemon Squeezy LLC, Wilmington, DE, USA",
        "5.1.03",
        "saas",
        1,
        299,
        299,
        ["Tailwind Plus, team license"],
        ambiguous=True,
    ),
    Merchant(
        "amzn_office",
        "AMZN MKTP US*{r}",
        "Amazon.com Services LLC",
        "410 Terry Ave N, Seattle, WA, USA",
        "5.1.08",
        "saas",
        1,
        90,
        260,
        ["Anker USB-C Hub, 3 units"],
        ambiguous=True,
    ),
    Merchant(
        "amzn_book",
        "AMZN MKTP US*{r}",
        "Amazon.com Services LLC",
        "410 Terry Ave N, Seattle, WA, USA",
        "5.1.09",
        "saas",
        1,
        15,
        45,
        ["Inspired, 2nd Edition (Kindle edition)"],
        ambiguous=True,
    ),
    Merchant(
        "apple",
        "APPLE.COM/BILL",
        "Apple Services",
        "One Apple Park Way, Cupertino, CA, USA",
        "5.1.03",
        "saas",
        1,
        10,
        10,
        ["iCloud+ 2 TB, monthly"],
        ambiguous=True,
    ),
    Merchant(
        "wework",
        "WEWORK MEXICO",
        "WeWork",
        "Av. Paseo de la Reforma, Mexico City, Mexico",
        "5.1.08",
        "saas",
        1,
        25,
        60,
        ["Day pass, coworking"],
        ambiguous=True,
    ),
    Merchant(
        "productcamp",
        "TICKETTAILOR* PRODUCTCAMP",
        "Product Camp Buenos Aires",
        "Buenos Aires, Argentina",
        "5.1.07",
        "es",
        1,
        30,
        90,
        ["Entrada general Product Camp"],
        ambiguous=True,
    ),
    Merchant(
        "gumroad",
        "GUMROAD.COM* SHAPEUP",
        "Gumroad",
        "548 Market St, San Francisco, CA, USA",
        "5.1.09",
        "saas",
        1,
        25,
        60,
        ["Shape Up handbook bundle"],
        ambiguous=True,
    ),
    Merchant(
        "twilio",
        "TWILIO {r}",
        "Twilio Inc.",
        "101 Spear St, San Francisco, CA, USA",
        "5.1.02",
        "saas",
        2,
        40,
        320,
        ["Programmable SMS usage, August"],
        ambiguous=True,
    ),
    Merchant(
        "sendgrid",
        "SENDGRID",
        "Twilio SendGrid",
        "1801 California St, Denver, CO, USA",
        "5.1.02",
        "saas",
        1,
        90,
        90,
        ["Email API Pro plan"],
        ambiguous=True,
    ),
    Merchant(
        "upwork",
        "UPWORK *ESCROW {r}",
        "Upwork Global Inc.",
        "530 Lytton Ave, Palo Alto, CA, USA",
        "5.1.04",
        "saas",
        1,
        400,
        900,
        ["Contract: QA testing, milestone 1"],
        ambiguous=True,
    ),
    Merchant(
        "fiverr",
        "FIVERR",
        "Fiverr International",
        "8 Eliezer Kaplan St, Tel Aviv, Israel",
        "5.1.01",
        "saas",
        1,
        80,
        300,
        ["Explainer video script for the website"],
        ambiguous=True,
    ),
    Merchant(
        "airalo",
        "AIRALO",
        "Airalo",
        "Singapore",
        "5.1.05",
        "saas",
        1,
        11,
        26,
        ["eSIM United States, 10 GB"],
        ambiguous=True,
    ),
    Merchant(
        "dutyfree",
        "DUTY FREE AMERICAS {r}",
        "Duty Free Americas",
        "Miami International Airport, FL, USA",
        "5.1.06",
        "pos",
        1,
        60,
        180,
        [],
        ambiguous=True,
        memo="gift for client in Sao Paulo",
    ),
    Merchant(
        "bestbuy",
        "BEST BUY 00012",
        "Best Buy",
        "1131 4th St SW, Washington, DC, USA",
        "5.1.08",
        "pos",
        1,
        70,
        130,
        [],
        ambiguous=True,
    ),
    Merchant(
        "economist",
        "THE ECONOMIST",
        "The Economist Newspaper Ltd",
        "The Adelphi, London, UK",
        "5.1.09",
        "saas",
        1,
        22,
        22,
        ["Digital subscription, monthly"],
        ambiguous=True,
    ),
    Merchant(
        "betalist",
        "BETALIST",
        "BetaList",
        "Remote",
        "5.1.01",
        "saas",
        1,
        129,
        129,
        ["Featured startup listing"],
        ambiguous=True,
    ),
    Merchant(
        "namecheap",
        "NAMECHEAP.COM",
        "Namecheap, Inc.",
        "4600 East Washington St, Phoenix, AZ, USA",
        "5.1.02",
        "saas",
        1,
        35,
        70,
        ["Domain renewal andeslabs.io, 1 year"],
        ambiguous=True,
    ),
    Merchant(
        "calendly",
        "CALENDLY",
        "Calendly LLC",
        "115 E Main St, Buford, GA, USA",
        "5.1.03",
        "saas",
        1,
        60,
        80,
        ["Teams plan, 5 seats"],
        ambiguous=True,
    ),
    Merchant(
        "stickermule",
        "STICKERMULE.COM",
        "Sticker Mule",
        "1 Sticker Mule Plaza, Amsterdam, NY, USA",
        "5.1.01",
        "saas",
        1,
        150,
        400,
        ["Die cut stickers with logo, 1000 units"],
        ambiguous=True,
    ),
    Merchant(
        "doordash",
        "DD *DOORDASH {r}",
        "DoorDash",
        "303 2nd St, San Francisco, CA, USA",
        "5.1.06",
        "saas",
        1,
        60,
        220,
        ["Delivery order"],
        ambiguous=True,
        memo="team dinner",
    ),
    Merchant(
        "lyft",
        "LYFT *RIDE {r}",
        "Lyft, Inc.",
        "185 Berry St, San Francisco, CA, USA",
        "5.1.05",
        "saas",
        2,
        9,
        45,
        ["Ride"],
        ambiguous=True,
    ),
    Merchant(
        "costco",
        "COSTCO WHSE #0144",
        "Costco Wholesale",
        "450 10th St, San Francisco, CA, USA",
        "5.1.06",
        "pos",
        1,
        80,
        240,
        [],
        ambiguous=True,
        memo="offsite snacks",
    ),
]

RESTAURANTS = [
    ("Joe's Pizza", "1435 Broadway, New York, NY"),
    ("Sweetgreen Market St", "171 2nd St, San Francisco, CA"),
    ("Tartine Bakery", "600 Guerrero St, San Francisco, CA"),
    ("The Smith Midtown", "956 2nd Ave, New York, NY"),
    ("Coya Miami", "999 Brickell Ave, Miami, FL"),
    ("Shake Shack Madison", "Madison Square Park, New York, NY"),
    ("La Mar Cebicheria", "Pier 1.5, San Francisco, CA"),
    ("Zuma Miami", "270 Biscayne Blvd Way, Miami, FL"),
]
MEALS = [
    "Lunch special",
    "Burger",
    "Salad bowl",
    "Ceviche",
    "Pizza slice x2",
    "Pasta",
    "Sparkling water",
    "Coffee",
    "Iced tea",
    "Dessert",
    "Tacos",
    "Grain bowl",
]
COFFEE = ["Latte", "Cappuccino", "Cold brew", "Croissant", "Muffin", "Americano"]

CONTRACTORS = [
    ("Tomasz Nowak", "Krakow, Poland", "saas", 4200, "Backend development"),
    ("Ana Ribeiro", "Lisbon, Portugal", "saas", 3600, "Product design"),
    ("Daniel Okafor", "Lagos, Nigeria", "saas", 2800, "Mobile development"),
    ("Priya Raman", "Bangalore, India", "saas", 3100, "Data engineering"),
    ("Mateo Silva", "Montevideo, Uruguay", "es", 3400, "Desarrollo frontend"),
    ("Camila Restrepo", "Medellín, Colombia", "es", 2600, "Soporte a clientes"),
    ("Ivan Petrenko", "Lviv, Ukraine", "saas", 3900, "DevOps"),
    ("Sara Lindqvist", "Stockholm, Sweden", "saas", 5200, "Growth marketing"),
    ("Laura Méndez", "Ciudad de México, México", "es", 3000, "Contenido y SEO"),
    ("Andrei Popescu", "Bucharest, Romania", "saas", 3300, "QA automation"),
    ("Lucas Moreau", "Lyon, France", "saas", 4600, "Machine learning"),
    ("Bruno Costa", "Porto Alegre, Brazil", "saas", 2900, "Customer success"),
    ("Emily Carter", "Manchester, UK", "saas", 4100, "Technical writing"),
    ("Nikhil Rao", "Pune, India", "saas", 2700, "Backend development"),
    ("Fatima Alaoui", "Casablanca, Morocco", "saas", 2500, "Illustration"),
    ("Kenji Watanabe", "Osaka, Japan", "saas", 4800, "Security review"),
]


@dataclass
class Txn:
    posted: date
    type: str
    descriptor: str
    amount: int
    currency: str
    cardholder: str = ""
    card_last4: str = ""
    memo: str = ""
    extra: dict = field(default_factory=dict)
    truth: dict = field(default_factory=dict)
    receipt: dict | None = None
    id: str = ""


def _day(n: int) -> date:
    return date(YEAR, MONTH, n)


def _ref(rng: random.Random, n: int = 5) -> str:
    return "".join(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(n))


def _split(rng: random.Random, total: int, parts: int) -> list[int]:
    if parts == 1:
        return [total]
    cuts = sorted(rng.sample(range(100, total - 100), parts - 1)) if total > 100 * parts else []
    if not cuts:
        return [total]
    pieces, prev = [], 0
    for cut in [*cuts, total]:
        pieces.append(cut - prev)
        prev = cut
    return pieces


def _receipt_date(rng: random.Random, posted: date) -> date:
    return posted - timedelta(days=rng.choice([0, 0, 1, 1, 2]))


def _card_txns(rng: random.Random) -> list[Txn]:
    out = []
    for m in COVERED + AMBIGUOUS:
        for i in range(m.count):
            day = m.days[i] if m.days else rng.randint(1, 30)
            posted = _day(day)
            holder, last4 = rng.choice(CARDHOLDERS)
            ref = _ref(rng)
            descriptor = m.descriptor.replace("{r}", ref)
            vendor, address = m.vendor, m.address
            if m.key == "toast":
                vendor, address = rng.choice(RESTAURANTS)
                descriptor = "TST* " + vendor.upper().replace("'", "")[:18]
            amount = rng.randint(m.lo * 100, m.hi * 100)
            if m.lo == m.hi:
                amount = m.lo * 100 - 1 if m.lo < 50 else m.lo * 100
            rdate = _receipt_date(rng, posted)
            receipt = {
                "layout": m.layout if m.layout in ("saas", "es", "pos") else "travel",
                "vendor": vendor,
                "address": address,
                "date": rdate,
                "currency": "USD",
                "card_last4": last4,
                "number": f"{rng.randint(1000, 9999)}-{_ref(rng, 6)}",
            }
            if m.layout in ("saas", "es"):
                item = m.items[i % len(m.items)]
                if m.key == "uber":
                    item = f"Trip, {rng.choice(['San Francisco', 'New York', 'Miami', 'Sao Paulo'])}"
                receipt["items"] = [(item, amount)]
                receipt["total_cents"] = amount
            elif m.layout == "pos":
                amount, receipt = _pos_receipt(rng, m, receipt, amount)
            elif m.layout == "flight":
                fare = amount * 85 // 100
                receipt.update(
                    kind="flight",
                    vendor=vendor,
                    passenger=_passenger(holder),
                    route=rng.choice(["EZE MIA EZE", "EZE JFK EZE", "EZE PTY SFO"]),
                    items=[(m.items[0], fare), (m.items[1], amount - fare)],
                    total_cents=amount,
                )
            elif m.layout == "hotel":
                nights = rng.randint(2, 4)
                arrival = posted - timedelta(days=nights + rng.choice([0, 1]))
                rdate = arrival + timedelta(days=nights)
                parts = [amount // nights] * nights
                parts[-1] += amount - sum(parts)
                receipt.update(
                    kind="hotel",
                    date=rdate,
                    arrival=arrival,
                    passenger=holder,
                    room=str(rng.randint(301, 1890)),
                    items=[(f"Room rate night {n + 1}", p) for n, p in enumerate(parts)],
                    total_cents=amount,
                )
            memo = m.memo
            if not memo and rng.random() < 0.15:
                memo = rng.choice(["", "client meeting", "trip to Sao Paulo", "team offsite", ""])
            t = Txn(
                posted=posted,
                type="card_purchase",
                descriptor=descriptor,
                amount=amount,
                currency="USD",
                cardholder=holder,
                card_last4=last4,
                memo=memo,
                truth={"account": m.account, "merchant_key": m.key, "ambiguous": m.ambiguous, "anomalies": []},
                receipt=receipt,
            )
            out.append(t)
    return out


def _passenger(name: str) -> str:
    first, last = name.split(" ", 1)
    return f"{last.upper()}/{first.upper()}"


def _pos_receipt(rng: random.Random, m: Merchant, receipt: dict, amount: int):
    menu = COFFEE if m.key in ("starbucks", "bluebottle") else MEALS
    if m.key == "dutyfree":
        menu = ["Gift set, chocolates", "Gift set, wine"]
    if m.key == "bestbuy":
        menu = ["Logitech C920 webcam", "USB-C cable 2m"]
    if m.key == "costco":
        menu = ["Snack variety pack", "Sparkling water 24ct", "Fruit tray"]
    subtotal = amount * 100 // 125 if m.tip else amount * 100 // 109
    tax = subtotal * 8875 // 100000
    tip = amount - subtotal - tax if m.tip else 0
    if not m.tip:
        tax = amount - subtotal
    n_items = rng.randint(1, min(3, len(menu)))
    names = rng.sample(menu, n_items)
    parts = _split(rng, subtotal, n_items)
    if len(parts) != n_items:
        names = names[: len(parts)]
    receipt.update(
        layout="pos",
        items=list(zip(names, parts, strict=True)),
        subtotal_cents=subtotal,
        tax_cents=tax,
        tip_cents=tip,
        total_cents=amount,
        time=f"{rng.randint(11, 21)}:{rng.randint(0, 59):02d}",
    )
    if m.key == "starbucks":
        receipt["vendor"] = "Starbucks Coffee Company"
        receipt["address"] = rng.choice(["Store 2131, Miami, FL", "Store 0870, New York, NY"])
    return amount, receipt


def _payouts(rng: random.Random) -> list[Txn]:
    out = []
    plan = [(c, 30) for c in CONTRACTORS] + [
        (CONTRACTORS[0], 15),
        (CONTRACTORS[7], 15),
        (CONTRACTORS[10], 12),
        (CONTRACTORS[15], 22),
    ]
    for (name, city, layout, base, service), day in plan:
        posted = _day(day if day != 30 else rng.choice([29, 30]))
        amount = (base + rng.choice([0, 0, 0, 100, 250, -150])) * 100
        wallet = (
            "0x"
            + "".join(rng.choice("0123456789abcdef") for _ in range(4))
            + "…"
            + "".join(rng.choice("0123456789abcdef") for _ in range(4))
        )
        number = f"{name.split()[0][:2].upper()}{name.split()[-1][:2].upper()}-2026-{rng.randint(9, 99):02d}"
        period = "September 2026" if day >= 28 else "milestone, September 2026"
        item = f"{service}, {period}" if layout == "saas" else f"{service}, septiembre 2026"
        receipt = {
            "layout": layout,
            "kind": "invoice",
            "vendor": name,
            "address": city,
            "date": posted - timedelta(days=rng.choice([1, 2, 3])),
            "currency": "USDC",
            "number": number,
            "items": [(item, amount)],
            "total_cents": amount,
            "footer": "Payment in USDC to the wallet on file",
        }
        out.append(
            Txn(
                posted=posted,
                type="usdc_payout",
                descriptor=f"USDC PAYOUT {name.upper()}",
                amount=amount,
                currency="USDC",
                extra={"counterparty": name, "wallet": wallet, "reference": number},
                truth={"account": "5.1.04", "merchant_key": "contractor", "ambiguous": False, "anomalies": []},
                receipt=receipt,
            )
        )
    return out


def _topups(rng: random.Random) -> list[Txn]:
    out = []
    for day, ars in ((2, 60_000_000), (15, 45_000_000), (29, 70_000_000)):
        posted = _day(day)
        crypto_rate = fx.rate(posted, "cripto")
        ars_cents = ars * 100
        usdc_cents = int(ars_cents / crypto_rate)  # rounded down, the exchange keeps the dust
        out.append(
            Txn(
                posted=posted,
                type="ars_topup",
                descriptor="TOP UP FROM BANK TRANSFER ARS",
                amount=ars_cents,
                currency="ARS",
                extra={
                    "credited_amount": cents_str(usdc_cents),
                    "credited_currency": "USDC",
                    "source_bank": "Local bank account ending 0457",
                },
                truth={"account": "1.1.02", "merchant_key": "topup", "ambiguous": False, "anomalies": []},
            )
        )
    return out


def _fees() -> list[Txn]:
    out = []
    for day, desc, amount in (
        (1, "CARD PROGRAM FEE SEP 2026", 25000),
        (12, "INTL TXN FEE", 1840),
        (23, "INTL TXN FEE", 2265),
        (30, "FX MARKUP FEE", 3110),
    ):
        out.append(
            Txn(
                posted=_day(day),
                type="card_fee",
                descriptor=desc,
                amount=amount,
                currency="USD",
                truth={"account": "5.1.10", "merchant_key": "fee", "ambiguous": False, "anomalies": []},
            )
        )
    return out


def _settlement(opening_card_cents: int) -> Txn:
    return Txn(
        posted=_day(5),
        type="card_settlement",
        descriptor="CARD STATEMENT PAYMENT AUG 2026",
        amount=opening_card_cents,
        currency="USDC",
        truth={"account": "2.1.01", "merchant_key": "settlement", "ambiguous": False, "anomalies": []},
    )


def _plant(rng: random.Random, card: list[Txn], payouts: list[Txn]) -> list[Txn]:
    """Plant anomalies on existing transactions and return the extra ones (duplicates, refunds)."""
    extra: list[Txn] = []
    taken: set[int] = set()

    def pick(pred, n):
        pool = [t for t in card if id(t) not in taken and pred(t)]
        chosen = rng.sample(pool, n)
        taken.update(id(t) for t in chosen)
        return chosen

    # Receipt amount differs from the charge.
    for t in pick(lambda t: t.truth["merchant_key"] == "toast", 3):
        r = t.receipt
        r["tip_blank"] = True
        r["total_cents"] = r["subtotal_cents"] + r["tax_cents"]
        t.truth["anomalies"].append("amount_mismatch")
        t.truth["mismatch_kind"] = "tip_added_after_receipt"
    for t in pick(lambda t: t.truth["merchant_key"] in ("marriott", "hilton"), 2):
        r = t.receipt
        less = rng.choice([4000, 6000, 8500])
        r["total_cents"] = t.amount - less
        r["items"][-1] = (r["items"][-1][0], r["items"][-1][1] - less)
        t.truth["anomalies"].append("amount_mismatch")
        t.truth["mismatch_kind"] = "hotel_folio_lower_than_charge"
    for t in pick(lambda t: t.truth["merchant_key"] in ("ubereats", "eventbrite", "udemy"), 2):
        r = t.receipt
        ars = convert(t.amount, fx.rate(t.posted))
        r.update(layout="es", currency="ARS", total_cents=ars, items=[(r["items"][0][0], ars)])
        t.truth["anomalies"].append("amount_mismatch")
        t.truth["mismatch_kind"] = "receipt_in_ars"
    for t in pick(lambda t: t.truth["merchant_key"] == "websummit", 1):
        r = t.receipt
        eur = t.amount * 92 // 100 // 100 * 100
        r.update(currency="EUR", total_cents=eur, items=[(r["items"][0][0], eur)])
        t.truth["anomalies"].append("amount_mismatch")
        t.truth["mismatch_kind"] = "receipt_in_eur"
    p = rng.choice(payouts)
    p.receipt["total_cents"] = p.amount + 5000
    p.receipt["items"] = [(p.receipt["items"][0][0], p.amount + 5000)]
    p.truth["anomalies"].append("amount_mismatch")
    p.truth["mismatch_kind"] = "invoice_differs_from_payout"

    # Missing receipts: 19 card purchases (6 of them with no rule) and one contractor invoice.
    for t in pick(lambda t: t.truth["ambiguous"] and t.truth["merchant_key"] not in ("lyft",), 6):
        t.receipt = None
        t.truth["anomalies"].append("missing_receipt")
    for t in pick(lambda t: not t.truth["ambiguous"] and t.truth["merchant_key"] not in ("websummit",), 13):
        t.receipt = None
        t.truth["anomalies"].append("missing_receipt")
    q = rng.choice([x for x in payouts if not x.truth["anomalies"]])
    q.receipt = None
    q.truth["anomalies"].append("missing_receipt")

    # Duplicate charges: same descriptor and amount, posted again, no second receipt.
    for t in pick(
        lambda t: t.truth["merchant_key"] in ("uber", "toast", "meta", "anthropic", "starbucks") and t.posted.day < 29,
        5,
    ):
        dup = Txn(
            posted=t.posted + timedelta(days=rng.choice([0, 1])),
            type="card_purchase",
            descriptor=t.descriptor,
            amount=t.amount,
            currency="USD",
            cardholder=t.cardholder,
            card_last4=t.card_last4,
            truth={
                "account": t.truth["account"],
                "merchant_key": t.truth["merchant_key"],
                "ambiguous": t.truth["ambiguous"],
                "anomalies": ["duplicate"],
                "duplicate_of": t,
            },
        )
        extra.append(dup)

    # A legitimate repeat: two rides with the same fare on the same day, each with its receipt.
    legit = pick(lambda t: t.truth["merchant_key"] == "uber" and t.receipt is not None, 1)[0]
    twin = Txn(
        posted=legit.posted,
        type="card_purchase",
        descriptor="UBER *TRIP " + _ref(rng),
        amount=legit.amount,
        currency="USD",
        cardholder=legit.cardholder,
        card_last4=legit.card_last4,
        truth={
            "account": "5.1.05",
            "merchant_key": "uber",
            "ambiguous": False,
            "anomalies": [],
            "legit_repeat_of": legit,
        },
        receipt={
            **legit.receipt,
            "number": f"{rng.randint(1000, 9999)}-{_ref(rng, 6)}",
            "items": [("Trip, return", legit.amount)],
        },
    )
    twin.descriptor = legit.descriptor
    extra.append(twin)

    # Refunds: three offset a September charge, one belongs to an August booking.
    for key, share in (("figma", 1.0), ("latam", 0.12), ("airbnb", 0.15)):
        orig = pick(lambda t, k=key: t.truth["merchant_key"] == k and t.posted.day < 24, 1)[0]
        amount = orig.amount if share == 1.0 else int(orig.amount * share)
        extra.append(
            Txn(
                posted=orig.posted + timedelta(days=rng.randint(2, 6)),
                type="card_refund",
                descriptor=orig.descriptor,
                amount=amount,
                currency="USD",
                cardholder=orig.cardholder,
                card_last4=orig.card_last4,
                truth={
                    "account": orig.truth["account"],
                    "merchant_key": key,
                    "ambiguous": False,
                    "anomalies": [],
                    "refund_of": orig,
                },
            )
        )
    extra.append(
        Txn(
            posted=_day(8),
            type="card_refund",
            descriptor="BOOKING.COM HOTEL",
            amount=21000,
            currency="USD",
            cardholder="Valentina Sosa",
            card_last4="7718",
            truth={
                "account": "5.1.05",
                "merchant_key": "booking",
                "ambiguous": False,
                "anomalies": ["refund_original_not_in_period"],
                "refund_of": None,
            },
        )
    )
    return extra


def _no_accidental_duplicates(rng: random.Random, txns: list[Txn]) -> None:
    """Re-roll card amounts that would look like duplicates without being planted."""
    seen: dict[tuple, Txn] = {}
    for t in sorted(txns, key=lambda t: t.posted):
        if t.type != "card_purchase" or "duplicate" in t.truth["anomalies"] or "legit_repeat_of" in t.truth:
            continue
        key = (t.descriptor.split()[0], t.amount)
        prev = seen.get(key)
        if prev and abs((t.posted - prev.posted).days) <= 3:
            raise RuntimeError(f"accidental duplicate {t.descriptor} {t.amount}")
        seen[key] = t


def build(seed: int = SEED) -> dict:
    rng = random.Random(seed)
    from pipeline.config import settings

    opening = settings()["opening_balances"]
    card = _card_txns(rng)
    payouts = _payouts(rng)
    extra = _plant(rng, card, payouts)
    txns = card + payouts + _topups(rng) + _fees() + [_settlement(to_cents(opening["card_payable_usd"]))] + extra
    _no_accidental_duplicates(rng, txns)

    order = {"card_settlement": 0, "ars_topup": 1}
    txns.sort(key=lambda t: (t.posted, order.get(t.type, 2), t.descriptor, t.amount))
    for i, t in enumerate(txns, 1):
        t.id = f"TX-{i:04d}"

    receipts = [t for t in txns if t.receipt is not None]
    rng.shuffle(receipts)
    for i, t in enumerate(receipts, 1):
        t.receipt["id"] = f"RC-{i:04d}"

    if RAW.exists():
        shutil.rmtree(RAW)
    RECEIPTS.mkdir(parents=True)
    TRUTH.mkdir(parents=True, exist_ok=True)

    export_rows, truth_tx, truth_rc = [], {}, {}
    for t in txns:
        row = {
            "id": t.id,
            "posted_at": t.posted.isoformat(),
            "type": t.type,
            "descriptor": t.descriptor,
            "amount": cents_str(t.amount),
            "currency": t.currency,
        }
        if t.cardholder:
            row["cardholder"] = t.cardholder
            row["card_last4"] = t.card_last4
        if t.type.startswith("card_") and t.type != "card_settlement":
            row["memo"] = t.memo
        row.update(t.extra)
        export_rows.append(row)
        tr = {
            "account": t.truth["account"],
            "receipt_id": t.receipt["id"] if t.receipt else None,
            "anomalies": sorted(t.truth["anomalies"]),
            "ambiguous_merchant": t.truth["ambiguous"],
            "merchant_key": t.truth["merchant_key"],
        }
        if "mismatch_kind" in t.truth:
            tr["mismatch_kind"] = t.truth["mismatch_kind"]
        if "duplicate_of" in t.truth:
            tr["duplicate_of"] = t.truth["duplicate_of"].id
        if "legit_repeat_of" in t.truth:
            tr["legit_repeat_of"] = t.truth["legit_repeat_of"].id
        if "refund_of" in t.truth:
            tr["refund_of"] = t.truth["refund_of"].id if t.truth["refund_of"] else None
        truth_tx[t.id] = tr
        if t.receipt:
            r = t.receipt
            render(r, RECEIPTS / f"{r['id']}.pdf")
            truth_rc[r["id"]] = {
                "txn_id": t.id,
                "vendor": r["vendor"],
                "date": r["date"].isoformat(),
                "amount": cents_str(r["total_cents"]),
                "currency": r["currency"],
                "layout": r["layout"] if r["layout"] != "travel" else r.get("kind", "travel"),
                "language": "es" if r["layout"] == "es" else "en",
            }

    export = {
        "format": "assumed export format (invented for this prototype, not a real API)",
        "account_holder": "Andes Labs SRL (fictional)",
        "period": f"{YEAR}-{MONTH:02d}",
        "generated_by": f"pipeline/generate.py seed {seed}",
        "transactions": export_rows,
    }
    write_json(RAW / "transactions.json", export)
    truth = {
        "note": "Ground truth written by the generator. The engine and the AI never read it.",
        "seed": seed,
        "transactions": truth_tx,
        "receipts": dict(sorted(truth_rc.items())),
    }
    write_json(TRUTH / "ground_truth.json", truth)
    counts: dict[str, int] = {}
    for tr in truth_tx.values():
        for a in tr["anomalies"]:
            counts[a] = counts.get(a, 0) + 1
    return {
        "transactions": len(txns),
        "receipts": len(truth_rc),
        "ambiguous_merchants": sum(1 for tr in truth_tx.values() if tr["ambiguous_merchant"]),
        "planted": counts,
    }
