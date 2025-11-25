# Cron Job Setup for Monthly Updates

## Quick Setup

Run this command to set up monthly automatic updates:

```bash
(crontab -l 2>/dev/null; echo "0 9 1 * * /Users/savantlab/mental-rotation-research/scripts/cron_update.sh") | crontab -
```

This will:
- Run on the **1st of every month at 9:00 AM**
- Check for new mental rotation publications
- Automatically merge with existing data
- Save logs to `logs/` directory

## Verify Cron Job

Check if cron job is installed:
```bash
crontab -l
```

You should see:
```
0 9 1 * * /Users/savantlab/mental-rotation-research/scripts/cron_update.sh
```

## Cron Schedule Explanation

```
0 9 1 * *
│ │ │ │ │
│ │ │ │ └── Day of week (0-7, both 0 and 7 = Sunday)
│ │ │ └──── Month (1-12)
│ │ └────── Day of month (1-31)
│ └──────── Hour (0-23)
└────────── Minute (0-59)
```

Current setting: `0 9 1 * *` = 9:00 AM on the 1st of every month

## Alternative Schedules

**Every 1st and 15th at 9 AM:**
```bash
0 9 1,15 * * /Users/savantlab/mental-rotation-research/scripts/cron_update.sh
```

**Every Monday at 9 AM:**
```bash
0 9 * * 1 /Users/savantlab/mental-rotation-research/scripts/cron_update.sh
```

**First Monday of every month at 9 AM:**
```bash
0 9 1-7 * 1 /Users/savantlab/mental-rotation-research/scripts/cron_update.sh
```

## Manually Run Update

Test the update script manually:
```bash
/Users/savantlab/mental-rotation-research/scripts/cron_update.sh
```

## Check Logs

View the most recent update log:
```bash
ls -lt ~/mental-rotation-research/logs/ | head -5
cat ~/mental-rotation-research/logs/update_*.log
```

## Remove Cron Job

If you want to disable automatic updates:
```bash
crontab -l | grep -v "cron_update.sh" | crontab -
```

## Troubleshooting

**Cron not running?**
1. Check if cron has Full Disk Access:
   - System Preferences → Security & Privacy → Privacy → Full Disk Access
   - Add `/usr/sbin/cron` if not present

2. Check system logs:
   ```bash
   log show --predicate 'process == "cron"' --last 1d
   ```

**Script errors?**
Check the log files in `logs/` directory for error messages.

## What the Script Does

1. Changes to project directory
2. Activates Python virtual environment
3. Runs `update_current_year.py`
4. Logs all output to timestamped log file
5. Cleans up logs older than 1 year
