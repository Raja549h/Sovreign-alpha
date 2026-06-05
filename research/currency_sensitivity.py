"""
Currency Sensitivity Mapping — INR/USD exposure per company
=============================================================
Classifies each holding by currency vulnerability based on
sector profile, revenue stream, and import dependence.
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone

SECTOR_PROFILES = {
    'NBFC': {
        'fx_revenue': 'LOW', 'import_dependence': 'LOW',
        'usd_debt_risk': 'LOW', 'overall': 'LOW'
    },
    'BANK': {
        'fx_revenue': 'LOW', 'import_dependence': 'LOW',
        'usd_debt_risk': 'MEDIUM', 'overall': 'LOW'
    },
    'Gold Loan NBFC': {
        'fx_revenue': 'LOW', 'import_dependence': 'LOW',
        'gold_price_link': 'HIGH', 'overall': 'MEDIUM'
    },
    'Consumer Brands': {
        'fx_revenue': 'LOW', 'import_dependence': 'MEDIUM',
        'license_fee_usd': 'MEDIUM', 'overall': 'MEDIUM'
    },
    'Consumer': {
        'fx_revenue': 'LOW', 'import_dependence': 'MEDIUM',
        'license_fee_usd': 'MEDIUM', 'overall': 'MEDIUM'
    },
    'FMCG': {
        'fx_revenue': 'LOW', 'import_dependence': 'MEDIUM',
        'raw_material_import': 'MEDIUM', 'overall': 'MEDIUM'
    },
    'IT': {
        'fx_revenue': 'HIGH', 'import_dependence': 'LOW',
        'overall': 'HIGH_BENEFICIARY'
    },
    'TECHNOLOGY': {
        'fx_revenue': 'HIGH', 'import_dependence': 'LOW',
        'overall': 'HIGH_BENEFICIARY'
    },
    'Pharma': {
        'fx_revenue': 'HIGH', 'import_dependence': 'MEDIUM',
        'overall': 'MODERATE_BENEFICIARY'
    },
    'Auto': {
        'fx_revenue': 'LOW', 'import_dependence': 'HIGH',
        'overall': 'VULNERABLE'
    },
    'ENERGY': {
        'fx_revenue': 'LOW', 'import_dependence': 'HIGH',
        'overall': 'VULNERABLE'
    },
    'INFRASTRUCTURE': {
        'fx_revenue': 'LOW', 'import_dependence': 'MEDIUM',
        'usd_debt_risk': 'HIGH', 'overall': 'VULNERABLE'
    },
    'METALS': {
        'fx_revenue': 'MEDIUM', 'import_dependence': 'MEDIUM',
        'commodity_link': 'HIGH', 'overall': 'MEDIUM'
    },
    'REALTY': {
        'fx_revenue': 'LOW', 'import_dependence': 'LOW',
        'overall': 'LOW'
    },
}


class CurrencySensitivity:

    def assess_company(self, ticker: str, company_name: str, sector: str) -> Dict:
        profile = SECTOR_PROFILES.get(sector, SECTOR_PROFILES.get('NBFC'))
        overall = profile.get('overall', 'LOW')

        classification = 'NEUTRAL'
        if 'BENEFICIARY' in overall:
            classification = 'BENEFICIARY'
        elif overall == 'VULNERABLE':
            classification = 'VULNERABLE'

        sensitivity = 'LOW'
        if overall in ('HIGH_BENEFICIARY', 'VULNERABLE'):
            sensitivity = 'HIGH'
        elif overall in ('MODERATE_BENEFICIARY', 'MEDIUM'):
            sensitivity = 'MEDIUM'

        primary_exposure = self._determine_primary_exposure(profile)
        inr_weak, inr_strong = self._describe_impacts(profile, overall)

        flag = overall in ('VULNERABLE',)
        flag_text = ''
        if flag:
            flag_text = (
                f"{ticker} ({sector}) carries {sensitivity} currency risk. "
                f"{primary_exposure}. INR weakness directly impacts margins."
            )

        return {
            'ticker': ticker, 'company_name': company_name, 'sector': sector,
            'sensitivity': sensitivity, 'classification': classification,
            'primary_exposure': primary_exposure,
            'inr_weakening_impact': inr_weak,
            'inr_strengthening_impact': inr_strong,
            'flag': flag, 'flag_text': flag_text
        }

    def generate_currency_flag(self, ticker: str, current_inr_usd: float, regime: str) -> Optional[str]:
        try:
            import yfinance as yf
            usdinr = yf.download('USDINR=X', period='1mo', interval='1d', progress=False)
            if usdinr.empty:
                return None
            start_price = float(usdinr['Close'].iloc[0])
            end_price = float(usdinr['Close'].iloc[-1])
            change_pct = round((end_price - start_price) / start_price * 100, 2)

            if abs(change_pct) < 0.5:
                return None

            from research.storage.research_db import get_all_companies
            companies = get_all_companies()
            company = next((c for c in companies if c.get('ticker', '').upper() == ticker.upper()), None)
            if not company:
                return None
            sector = company.get('sector', 'NBFC')
            profile = SECTOR_PROFILES.get(sector, SECTOR_PROFILES.get('NBFC'))
            overall = profile.get('overall', 'LOW')

            if change_pct > 0:
                if overall in ('VULNERABLE',):
                    return (
                        f"INR weakness of {change_pct}% over 30 days "
                        f"creates input cost headwind for {ticker} ({sector}). "
                        f"{self._determine_primary_exposure(profile)}."
                    )
                if 'BENEFICIARY' in overall:
                    return (
                        f"INR weakness of {change_pct}% benefits {ticker} "
                        f"through {profile.get('fx_revenue', 'HIGH')} USD-denominated revenue."
                    )
            elif change_pct < 0:
                if 'BENEFICIARY' in overall:
                    return (
                        f"INR strengthening of {abs(change_pct)}% over 30 days "
                        f"creates headwind for {ticker}'s USD-denominated revenue."
                    )
        except Exception:
            pass
        return None

    def assess_portfolio(self, companies: List[Dict]) -> Dict:
        vulnerable = []
        beneficiaries = []
        neutral = []
        for c in companies:
            result = self.assess_company(c.get('ticker', ''), c.get('company_name', ''), c.get('sector', 'NBFC'))
            if result['classification'] == 'VULNERABLE':
                vulnerable.append(result)
            elif result['classification'] == 'BENEFICIARY':
                beneficiaries.append(result)
            else:
                neutral.append(result)
        return {
            'vulnerable': vulnerable, 'beneficiaries': beneficiaries,
            'neutral': neutral,
            'total_vulnerable': len(vulnerable),
            'total_beneficiaries': len(beneficiaries),
            'total_neutral': len(neutral),
        }

    def _determine_primary_exposure(self, profile: Dict) -> str:
        if profile.get('fx_revenue') == 'HIGH':
            return 'Primary exposure: USD-denominated revenue stream'
        if profile.get('import_dependence') == 'HIGH':
            return 'Primary exposure: USD-denominated import costs'
        if profile.get('usd_debt_risk') == 'HIGH':
            return 'Primary exposure: USD-denominated debt servicing'
        if profile.get('gold_price_link') == 'HIGH':
            return 'Primary exposure: Gold price sensitivity (INR-denominated)'
        if profile.get('license_fee_usd') == 'MEDIUM':
            return 'Primary exposure: License fees partly linked to USD'
        if profile.get('raw_material_import') == 'MEDIUM':
            return 'Primary exposure: Imported raw material costs'
        if profile.get('commodity_link') == 'HIGH':
            return 'Primary exposure: Global commodity price linkage'
        return 'Minimal direct INR/USD exposure'

    def _describe_impacts(self, profile: Dict, overall: str) -> tuple:
        if 'BENEFICIARY' in overall:
            return (
                'Margin expansion from USD revenue conversion',
                'Margin compression as USD revenue translates to fewer INR'
            )
        if overall == 'VULNERABLE':
            return (
                'Input cost inflation from USD-denominated imports',
                'Marginal input cost relief'
            )
        return (
            'Limited direct impact from moderate USD exposure',
            'Limited direct impact from moderate USD exposure'
        )
