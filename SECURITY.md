# Security

## Untrusted input

`extract_signals.py` downloads third-party web pages. Everything it returns is data.
The skills instruct the agent to treat competitor content as material to analyse,
never as instructions, regardless of what the page says. If you find a way for page
content to change the agent's behaviour through this toolchain, please report it.

## Data handling

The scripts make outbound HTTP requests only to the URLs you pass on the command line.
They send a generic User-Agent and nothing else. They store nothing outside the
paths you specify. There is no telemetry.

## Reporting

Open a GitHub issue with the label `security`. For anything that should not be
public, use the repository's private vulnerability reporting if it is enabled.
