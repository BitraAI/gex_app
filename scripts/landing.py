"""Robinhood-style landing page for GammaEx (gex_app).

Rendered while no user is signed in: promo bar, sticky nav, oversized
tight-tracked hero, feature cards built from the app's real screenshots,
a dark band, trust cards, the magic-link log-in card (Streamlit widgets so
validation just works), and a legal footer.

Brand tokens lifted from robinhood.com's stylesheet: primary green
``--rh__primary-base`` = #00c805, ink #040d14, neutral greys #f4f4f5/#e6e6e6,
pill CTAs, and huge tight serif-free headlines.
"""
import logging
import os

import streamlit as st

from scripts import auth_db, mailer, persistent_session

log = logging.getLogger("gex.landing")

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STATIC_DIR = os.path.join(_BASE, "static")
_LANDING_DIR = os.path.join(_STATIC_DIR, "landing")

_HERO_IMAGE = "Candlesticks.png"
_FEATURES = [
    ("Candlesticks.png", "Candlesticks", "Institutional charts: live streaming bars, Andean oscillator, Half Trend, VPVR — pan both axes, zoom anything."),
    ("OrderFlow.png", "Order Flow", "Real-time ATM flow grid: book imbalance, absorption, conviction scoring, and wall-zone alerts, second by second."),
    ("TradeSignals.png", "Signals", "A strategy engine that scores every expiration and hands you ranked trade cards with reasoning attached."),
    ("Metrics.png", "Metrics", "GEX by strike, by expiration, flip points, and delta-weighted net flow — refreshed while the market breathes."),
    ("Volatility.png", "Volatility", "ATM implied vol by expiration and by strike, benchmarked against realized vol, with a variance-risk-premium view and an expiration-range slider."),
    ("MarketStructure.png", "Market Structure", "GEX by strike and by expiration, an expandable gamma surface, and the dealer curve — Call Wall and Put Wall strikes pinned right on the chart."),
    ("OptionsData.png", "Options Data", "A sortable full-chain grid: gamma, OI, volume, SSVI IV and richness per strike — ATM row, wall strikes, and max-pain highlighted, CSV export built in."),
    ("Positioning.png", "Positioning", "Call vs put open interest across every strike with the spot line drawn through — one toggle swaps the whole layout to volume."),
    ("UnusualTrades.png", "Unusual Trades", "A scanner across all tracked tickers: min volume, Vol/OI, premium, and DTE filters that surface the options activity that doesn't belong."),
]

def _ensure_landing_images() -> bool:
    """Verify every screenshot referenced by the landing page exists."""
    try:
        for name in [_HERO_IMAGE] + [f for f, _, _ in _FEATURES]:
            if not os.path.exists(os.path.join(_LANDING_DIR, name)):
                log.warning("Landing image missing: static/landing/%s", name)
                return False
        return True
    except Exception:
        return False


_FEATURE_CARDS = "".join(
    f"""
    <div class="feature-card">
      <div class="feature-media"><img src="/app/static/landing/{f}" alt="{title}"></div>
      <h3>{title}</h3>
      <p>{desc}</p>
    </div>"""
    for f, title, desc in _FEATURES
)


def _shell_html() -> str:
    return f"""
<div class="gh-rh-shell">

  <div class="promo-bar">Session data is live. <b>Analytics in one place.</b></div>

  <nav class="rh-nav">
    <div class="nav-inner">
      <a class="nav-logo" href="#top">
        <svg width="26" height="30" viewBox="0 0 21 28"><g fill="#00c805"><path d="M8.7 21.75l-.19.06c-1.19.39-2.94 1-4.51 1.72-.09.04-.14.15-.11.23.03.07.1.08.15.03l.19-.09c.43-.2.98-.51 1.55-.78l.02-.01c1.09-.51 2.32-1.09 3.06-1.44.01 0 .12-.06.18-.18l.55-1.1c.02-.03-.02-.07-.05-.06z"/><path d="M4.3 20.04c.08-.15.44-.84.52-1l.01-.02c2.4-4.51 5.34-8.78 8.71-12.66l.09-.11c.03-.04.03-.08.01-.12-.02-.04-.07-.06-.11-.05-.21.03-2.45.45-4.65.98-.22.06-.36.2-.39.23-1.65 1.97-3.21 4.04-4.65 6.14-.36.53-.7 1.05-1.03 1.57-.03.05-.01.12.05.15.66.4 1.13.8 1.45 1.07-1.43 1.02-2.53 2.03-3.3 2.82-.05.05-.03.13.04.15.37.11.98.29 1.7.47.21.05.37-.26.45-.32z"/><path d="M15.94 6.09c-.03-.05-.08-.07-.17-.05l-1.64.5-7.83 2.28c-.05.02-.08.06-.08.11 0 .05.03.09.08.1 2.36.7 5.09 1.71 7.58 2.83.05.02.1 0 .12-.04.09-.15.32-.52.44-.7 1.02-1.5 1.85-3.08 2.51-4.62.19-.45.06-.66-.01-.41z"/></g></svg>
        <span>GammaEx</span>
      </a>
      <div class="nav-links">
        <a href="#features">Product</a>
        <a href="#trust">Security</a>
        <a href="#open-account">Account</a>
      </div>
      <div class="nav-cta">
        <a class="nav-login" href="#open-account">Log in</a>
      </div>
    </div>
  </nav>

  <section class="hero" id="top">
    <div class="hero-inner">
      <div class="hero-copy">
        <h1>Decode the<br>options market</h1>
        <p>Manage your gamma exposure on GammaEx: dealer walls, real-time order
        flow, SSVI volatility, and ranked signals — stocks, ETFs, and index
        options, all in one place.</p>
        <div class="hero-cta">
          <a class="btn-pill btn-ghost" href="#features">Learn more</a>
        </div>
      </div>
      <div class="hero-media">
        <img src="/app/static/landing/{_HERO_IMAGE}" alt="GammaEx candlestick chart">
      </div>
    </div>

  </section>

  <section class="section" id="features">
    <div class="section-inner">
      <div class="section-head">
        <h2>One place to read<br>the gamma tape</h2>
        <p>Every tab is a different lens on the same live option chain —
        built for traders who want dealer context, not just charts.</p>
      </div>
      <div class="feature-grid">{_FEATURE_CARDS}</div>
    </div>
  </section>

  <section class="dark-band">
    <div class="dark-inner">
      <h2>Real-time flow.<br>Zero lag. No noise.</h2>
      <p>Level 2 option books stream straight into the grid — net flow,
      buy/sell splits, absorption, and conviction — at a 1-second cadence.</p>
      <a class="btn-pill btn-green" href="#open-account">Open your account</a>
    </div>
  </section>

  <section class="section" id="trust">
    <div class="section-inner">
      <div class="section-head">
        <h2>GammaEx Security Guarantee</h2>
        <p>We work hard to keep your data safe and local.</p>
      </div>
      <div class="trust-grid">
        <div class="trust-card"><h3>Your broker stays yours</h3><p>Credentials live in one local config file — they are never sent anywhere but Schwab.</p></div>
        <div class="trust-card"><h3>No passwords, ever</h3><p>Logins are one-time magic links — single-use, 30-minute tokens stored only as hashes in SQLite.</p></div>
        <div class="trust-card"><h3>SQLite-backed accounts</h3><p>One file, WAL journaling, strict constraints. Portable and auditable.</p></div>
        <div class="trust-card"><h3>Local-first analytics</h3><p>Tokens, candles, and flow state all stay on your own machine.</p></div>
      </div>
    </div>
  </section>

  </div>
</div>
"""


def _footer_html() -> str:
    return """
<div class="gh-rh-footer">
  <div class="footer-inner">
    <div class="footer-disc">
      <p><b>GammaEx is a local analytics tool, not a broker.</b> It reads your
      own Schwab API credentials and shows analytics derived from that data.
      Nothing here is investment advice and no orders are routed by this
      application. Options trading entails significant risk and is not
      appropriate for all customers. Review the Characteristics and Risks of
      Standardized Options before trading.</p>
      <p class="footer-copy">&copy; 2026 GammaEx Analytics. All rights reserved.</p>
    </div>
  </div>
</div>
"""


def _css() -> str:
    return """
<style>
:root {
  --gh-green: #00c805;
  --gh-green-hover: #00b302;
  --gh-ink: #040d14;
  --gh-mut: #5e6a72;
  --gh-bg: #ffffff;
  --gh-panel: #f7f7f8;
  --gh-line: #e6e6e6;
}
/* Clobber Streamlit chrome while the landing page is visible */
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { display: none !important; }
.stApp { background: var(--gh-bg); }
[data-testid="stMainBlockContainer"] {
  padding-top: 0 !important; padding-left: 0 !important;
  padding-right: 0 !important; max-width: none;
}

.gh-rh-shell { max-width: 1280px; margin: 0 auto; }

/* ---- promo bar ---- */
.promo-bar {
  background: var(--gh-ink); color: #fff; text-align: center;
  padding: 10px 16px; font-size: 14px;
}
.promo-bar a { color: var(--gh-green); font-weight: 700; text-decoration: none; }
.promo-bar b { color: var(--gh-green); }

/* ---- nav ---- */
.rh-nav {
  background: rgba(255,255,255,0.94);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--gh-line);
  position: sticky; top: 0; z-index: 999;
}
.nav-inner {
  max-width: 1280px; margin: 0 auto; padding: 12px 24px;
  display: flex; align-items: center; gap: 28px;
}
.nav-logo { display: flex; align-items: center; gap: 8px;
  font-weight: 800; font-size: 20px; color: var(--gh-ink);
  letter-spacing: -0.5px; text-decoration: none; }
.nav-links { display: flex; gap: 22px; flex: 1; }
.nav-links a { color: var(--gh-ink); text-decoration: none; font-weight: 600; font-size: 15px; }
.nav-links a:hover { color: var(--gh-green); }
.nav-cta { display: flex; align-items: center; gap: 14px; }
.nav-login { color: var(--gh-ink); font-weight: 600; text-decoration: none; font-size: 15px; }
.nav-login:hover { color: var(--gh-green); }

.btn-pill {
  display: inline-block; padding: 10px 22px; border-radius: 999px;
  font-weight: 700; font-size: 15px; text-decoration: none; line-height: 1.2;
  transition: transform .08s ease, background .15s ease;
}
.btn-pill:active { transform: scale(0.97); }
.btn-dark { background: var(--gh-ink); color: #fff; }
.btn-dark:hover { background: #1b2b38; }
.btn-green { background: var(--gh-green); color: var(--gh-ink); padding: 14px 30px; font-size: 17px; }
.btn-green:hover { background: var(--gh-green-hover); }
.btn-ghost { border: 1px solid var(--gh-ink); color: var(--gh-ink); padding: 13px 30px; font-size: 17px; }
.btn-ghost:hover { background: var(--gh-panel); }

/* ---- hero ---- */
.hero { padding: 48px 24px 0; }
.hero-inner {
  display: grid; grid-template-columns: 1fr 1.15fr; align-items: center; gap: 40px;
  max-width: 1240px; margin: 0 auto;
}
.hero-copy h1 {
  font-size: clamp(44px, 5.6vw, 76px); line-height: 1.02; letter-spacing: -0.03em;
  color: var(--gh-ink); margin: 0 0 18px; font-weight: 800;
}
.hero-copy p { font-size: 19px; line-height: 1.5; color: var(--gh-mut); margin: 0 0 26px; max-width: 460px; }
.hero-cta { display: flex; gap: 14px; flex-wrap: wrap; }
.hero-media img {
  width: 100%; border-radius: 20px;
  box-shadow: 0 30px 60px rgba(4,13,20,0.18), 0 4px 14px rgba(4,13,20,0.10);
  border: 1px solid var(--gh-line);
}

/* ---- sections ---- */
.section { padding: 72px 24px 0; }
.section-inner { max-width: 1240px; margin: 0 auto; }
.section-head h2 {
  font-size: clamp(32px, 3.4vw, 46px); letter-spacing: -0.02em;
  color: var(--gh-ink); margin: 0 0 10px; line-height: 1.08; font-weight: 800;
}
.section-head p { color: var(--gh-mut); font-size: 18px; margin: 0 0 34px; max-width: 640px; }

.feature-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; }
.feature-card {
  background: var(--gh-panel); border-radius: 18px; padding: 20px;
  border: 1px solid transparent; transition: border-color .15s ease, transform .15s ease;
}
.feature-card:hover { border-color: var(--gh-line); transform: translateY(-2px); }
.feature-card h3 { margin: 14px 0 6px; font-size: 20px; letter-spacing: -0.01em; color: var(--gh-ink); }
.feature-card p { margin: 0; color: var(--gh-mut); font-size: 15px; line-height: 1.5; }
.feature-media img { width: 100%; border-radius: 12px; display: block; aspect-ratio: 16/9; object-fit: cover; object-position: top left; }

/* ---- dark band ---- */
.dark-band { background: var(--gh-ink); margin-top: 72px; padding: 84px 24px; }
.dark-inner { max-width: 1240px; margin: 0 auto; }
.dark-inner h2 { color: #fff; font-size: clamp(36px, 4vw, 58px); letter-spacing: -0.03em; margin: 0 0 16px; line-height: 1.05; font-weight: 800; }
.dark-inner p { color: #aeb9c1; font-size: 19px; max-width: 560px; margin: 0 0 28px; }

/* ---- trust ---- */
.trust-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.trust-card { border-top: 3px solid var(--gh-green); padding: 18px 14px 0 0; }
.trust-card h3 { font-size: 17px; color: var(--gh-ink); margin: 0 0 8px; }
.trust-card p { font-size: 14.5px; color: var(--gh-mut); margin: 0; line-height: 1.55; }

/* ---- auth card (Streamlit widgets restyled) ---- */
.auth-wrap { max-width: 460px; margin: 54px auto 26px; padding: 0 24px; }
[data-testid="stForm"] {
  background: #fff; border: 1px solid var(--gh-line); border-radius: 20px;
  padding: 28px 30px 22px; box-shadow: 0 18px 44px rgba(4,13,20,0.08);
}
[data-testid="stForm"] label { font-weight: 600; color: var(--gh-ink) !important; font-size: 14px; }
[data-testid="stForm"] [data-testid="stTextInput"] input, [data-testid="stForm"] [data-testid="stTextInput"] input:focus {
  border-radius: 10px; border: 1.5px solid var(--gh-line); height: 44px;
}
[data-testid="stForm"] [data-testid="stTextInput"] input:focus { border-color: var(--gh-green); box-shadow: 0 0 0 1.5px rgba(0,200,5,.25); }
[data-testid="stFormSubmitButton"] > button {
  width: 100%; background: var(--gh-green) !important; color: var(--gh-ink) !important;
  border: none; border-radius: 999px; font-weight: 800; font-size: 16px; padding: 10px 0;
}
[data-testid="stFormSubmitButton"] > button:hover { background: var(--gh-green-hover) !important; }
.auth-title { text-align: center; margin: 0 0 4px; }
.auth-title h2 { font-size: 28px; letter-spacing: -0.02em; color: var(--gh-ink); margin: 0; font-weight: 800; }
.auth-title p { color: var(--gh-mut); margin: 6px 0 0; font-size: 15px; }

/* ---- footer ---- */
.gh-rh-footer { margin-top: 84px; border-top: 1px solid var(--gh-line); padding: 34px 24px 44px; }
.footer-inner { max-width: 1240px; margin: 0 auto; color: var(--gh-mut); font-size: 13px; line-height: 1.6; }
.footer-copy { margin-top: 22px; }

@media (max-width: 900px) {
  .hero-inner { grid-template-columns: 1fr; }
  .feature-grid { grid-template-columns: 1fr; }
  .trust-grid { grid-template-columns: 1fr 1fr; }
  .nav-links { display: none; }
}
</style>
"""


def _smtp_notice() -> None:
    """Hint for the operator when SMTP isn't set up: links land in the log."""
    st.caption(
        "Email delivery isn't configured. Add `smtp_host`, "
        "`smtp_port`, `smtp_user`, `smtp_password` under "
        "`[email]` in config.toml to send these links; the "
        "link was captured in the app log meanwhile."
    )


def _send_login_email(email: str) -> None:
    """Email a magic link for an account, or ask the admin to approve access.

    Unknown addresses never get a link directly — their request goes to the
    operator as an invitation e-mail. The same success wording is used both
    ways so the page doesn't reveal which emails are registered.
    """
    email = (email or "").strip()
    try:
        token = auth_db.create_login_token(email)
        if token is not None:
            link = mailer.magic_link(token)
            try:
                mailer.send_magic_link(email, link)
                st.success(f"Magic link sent to {email}. It is valid for 30 minutes.")
            except mailer.MailError as exc:
                # No SMTP / send failure: write the link to the app log so
                # the operator can still log the user in by hand.
                log.error("Magic link for %s: %s", email, link)
                st.error(str(exc))
                _smtp_notice()
        else:
            approval = auth_db.request_access(email)
            link = mailer.approve_link(approval)
            try:
                mailer.send_approval_request(email, link)
            except mailer.MailError as exc:
                # No SMTP / send failure: the administrator can pick the
                # approval link out of the app log and open it by hand.
                log.error("Approval link for %s: %s", email, link)
                st.error(str(exc))
                _smtp_notice()
            st.success(
                f"If {email} has an account, a magic link is on its way. "
                "Otherwise the administrator has been asked to approve your "
                "access — once approved, a login link will be emailed to you."
            )
    except auth_db.AuthError as exc:
        st.error(str(exc))


def _auth_card() -> None:
    # `?approve=<token>` — administrator approval of an access request.
    #   Creates the account and emails the user a magic link.
    approve_token = st.query_params.get("approve")
    if approve_token:
        try:
            approved_email = auth_db.approve_request(approve_token)
        except auth_db.AuthError as exc:
            st.error(str(exc))
        else:
            try:
                del st.query_params["approve"]
            except Exception:
                pass
            login_token = auth_db.create_login_token(approved_email)
            link = mailer.magic_link(login_token) if login_token else None
            if link:
                try:
                    mailer.send_magic_link(approved_email, link)
                    st.success(
                        f"Approved! An account was created for "
                        f"**{approved_email}** — a login link is on its way "
                        "to them (valid for 30 minutes)."
                    )
                except mailer.MailError as exc:
                    # No SMTP / send failure: the login link is in the app
                    # log to hand over by hand.
                    log.error("Magic link for %s: %s", approved_email, link)
                    st.error(str(exc))
                    _smtp_notice()
                    st.success(
                        f"Approved! An account was created for "
                        f"**{approved_email}**. The login link was captured "
                        "in the app log."
                    )
        return

    # `?login=<token>` — one-time magic link sent to an account's email.
    login_token = st.query_params.get("login")
    if login_token:
        try:
            user = auth_db.login_with_token(login_token)
        except auth_db.AuthError as exc:
            st.error(str(exc))
        else:
            try:
                del st.query_params["login"]
            except Exception:
                pass
            st.session_state["gex_user"] = user
            # Queue the persistent-session cookie: written on the next
            # dashboard run (see persistent_session.flush() in app.py).
            persistent_session.issue(user)
            st.rerun()
            return

    with st.form("gh_login_form", clear_on_submit=True):
        email = st.text_input("Email", key="gh_login_email",
                              placeholder="you@example.com")
        if st.form_submit_button("Send magic link", width="stretch"):
            _send_login_email(email)


def render_landing() -> None:
    """Draw the full Robinhood-style landing page and block sign-in state."""
    _ensure_landing_images()
    st.markdown(_shell_html(), unsafe_allow_html=True)

    st.markdown(
        """
<div class="auth-wrap" id="open-account">
  <div class="auth-title">
    <h2>Log in to GammaEx</h2>
    <p>One-time magic links, no password needed. First time? We'll ask
    the administrator to approve you.</p>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    _auth_card()
    st.markdown(_css(), unsafe_allow_html=True)
    st.markdown(_footer_html(), unsafe_allow_html=True)
    st.stop()
