# Cisco Catalyst 9600 VSL Network Health Audit

Automated Python health check and audit tool for Cisco Catalyst 9600-series (and IOS-XE) core and distribution switches operating in StackWise-Virtual (VSL) topologies. 

This script connects via SSH using Netmiko, collects critical performance and state diagnostics, and dispatches an aggregated report to **Cisco Webex Spaces** and an **SMTP email relay**.

---

## 📌 Features

- **VSL & Redundancy Monitoring**: Verifies StackWise-Virtual links and Dual-Active Detection (DAD) operational state.
- **BGP & Routing Audit**: Checks BGP neighbor session status.
- **Interface Health Check**: Collects interface states while suppressing `administratively down` noise to highlight operational ports (`up/up`) and physical outages (`down/down`).
- **Hardware & Environment Diagnostics**: Monitors active CPU load, power supplies, fan modules, and chassis temperatures.
- **Multi-Channel Alerting**: Sends markdown-formatted logs to Webex via Incoming Webhooks and plain-text reports via internal SMTP relays.

---

## 📋 Audit Commands Executed

The script runs the following sequence on target devices:

```text
1. show etherchannel summary
2. show stackwise-virtual
3. show stackwise-virtual dual-active-detection
4. show ip bgp summary
5. show ip interface brief | exclude administratively
6. show processes cpu sorted | ex 0.00
7. show environment all
