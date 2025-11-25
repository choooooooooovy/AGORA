from datetime import datetime, timezone, timedelta


# 한국 표준시 (KST = UTC+9)
KST = timezone(timedelta(hours=9))


def get_kst_now() -> datetime:
    return datetime.now(KST)


def get_kst_timestamp() -> str:
    return get_kst_now().isoformat()
