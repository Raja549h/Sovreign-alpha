# Sovereign Alpha 4D Scorer

Welcome to the open-source release of the core Sovereign Alpha 4D scoring algorithm. This lightweight module allows you to run the proprietary quantitative scoring model used in the institutional Sovereign Alpha platform.

## What is Sovereign Alpha?
Sovereign Alpha is an institutional intelligence operating system that helps professional investors identify variant perception, hidden risks, and non-consensus opportunities. It combines forensic equity research, portfolio intelligence, thesis tracking, and cryptographically verifiable predictions.

Check out the live platform here: [Sovereign Alpha Platform](https://huggingface.co/spaces/Raja549h/Sovereign-Alpha)

## Installation

1. Clone this repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```python
from scoring import FourDScorer

scorer = FourDScorer()

data = {
    'fundamental': {'earnings_growth': 15},
    'technical': {'rsi': 25},
    'sentiment': {'sentiment_index': 4.5},
    'macro': {'regime': 'RISK_ON'}
}

result = scorer.score(data)
print("Overall Score:", result['overall_score'])
```

## Contributing
Contributions are welcome! Please open an issue or pull request.
