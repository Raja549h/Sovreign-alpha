/**
 * Sovereign Alpha - Google Sheets Plugin
 * Fetches institutional intelligence directly into your spreadsheets.
 */

const BASE_URL = "http://127.0.0.1:5000/api/v1"; // Change to production URL when deployed

/**
 * Creates a custom menu when the spreadsheet is opened.
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Sovereign Alpha')
    .addItem('Refresh All Data', 'refreshData')
    .addToUi();
}

function refreshData() {
  SpreadsheetApp.getActiveSpreadsheet().toast('Data refreshed from Sovereign Alpha.', 'Status');
}

/**
 * Fetches the Sovereign Alpha 4D Score for a ticker.
 * @param {string} ticker The stock ticker symbol.
 * @return The formatted score and verdict.
 * @customfunction
 */
function SOVEREIGN_SCORE(ticker) {
  if (!ticker) return "Error: Missing ticker";
  try {
    const response = UrlFetchApp.fetch(`${BASE_URL}/score/${ticker}`);
    if (response.getResponseCode() !== 200) return "Error: API failed";
    const data = JSON.parse(response.getContentText());
    return `Score: ${data.overall_score}/5.0`;
  } catch (e) {
    return `Error: ${e.message}`;
  }
}

/**
 * Fetches recent divergence alerts.
 * @param {number} days Number of days to look back.
 * @return Formatted list of divergences.
 * @customfunction
 */
function SOVEREIGN_DIVERGENCES(days = 7) {
  try {
    const response = UrlFetchApp.fetch(`${BASE_URL}/divergences?days=${days}`);
    if (response.getResponseCode() !== 200) return "Error: API failed";
    const data = JSON.parse(response.getContentText());
    if (data.length === 0) return "No recent divergences";
    return data.map(d => `${d.ticker}: ${d.headline}`).join('\n');
  } catch (e) {
    return `Error: ${e.message}`;
  }
}

/**
 * Fetches summary statistics from the Validation Ledger.
 * @return Total, Hits, Misses, and Accuracy.
 * @customfunction
 */
function SOVEREIGN_VALIDATION_LEDGER() {
  try {
    const response = UrlFetchApp.fetch(`${BASE_URL}/validation-ledger?limit=100`);
    if (response.getResponseCode() !== 200) return "Error: API failed";
    const data = JSON.parse(response.getContentText());
    
    let hits = 0;
    let misses = 0;
    data.forEach(p => {
      if (p.actual_outcome === 'HIT') hits++;
      else if (p.actual_outcome === 'MISS') misses++;
    });
    
    const total = hits + misses;
    const accuracy = total > 0 ? ((hits / total) * 100).toFixed(1) : 0;
    
    return `Total: ${total} | HITs: ${hits} | MISSes: ${misses} | Accuracy: ${accuracy}%`;
  } catch (e) {
    return `Error: ${e.message}`;
  }
}
