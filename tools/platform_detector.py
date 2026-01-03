"""
Platform Detection Utility

Detects the current platform (Windows, Linux, Android/Termux, etc.)
to enable platform-specific connector selection.
"""

import os
import sys
import platform
from typing import Literal, Optional
from dataclasses import dataclass


PlatformType = Literal["windows", "linux", "android", "macos", "unknown"]


@dataclass
class PlatformInfo:
    """Information about the current platform."""
    
    platform_type: PlatformType
    is_termux: bool
    is_android: bool
    is_windows: bool
    is_linux: bool
    is_macos: bool
    system: str
    python_version: str
    architecture: str


def detect_termux() -> bool:
    """
    Detect if running in Termux environment.
    
    Returns:
        True if running in Termux
    """
    # Check for Termux-specific environment variables
    if os.getenv('TERMUX_VERSION') is not None:
        return True
    
    # Check for Termux prefix path
    if os.path.exists('/data/data/com.termux'):
        return True
    
    # Check PREFIX environment variable (Termux sets this)
    prefix = os.getenv('PREFIX', '')
    if 'com.termux' in prefix:
        return True
    
    return False


def detect_android() -> bool:
    """
    Detect if running on Android.
    
    Returns:
        True if running on Android
    """
    # First check for Termux (most common way to run Python on Android)
    if detect_termux():
        return True
    
    # Check for Android-specific paths
    android_indicators = [
        '/system/bin/app_process',
        '/system/bin/dalvikvm',
        '/system/framework/framework.jar',
    ]
    
    for indicator in android_indicators:
        if os.path.exists(indicator):
            return True
    
    # Check environment variables
    if os.getenv('ANDROID_ROOT') or os.getenv('ANDROID_DATA'):
        return True
    
    # Check for common Android properties
    try:
        if os.path.exists('/system/build.prop'):
            return True
    except Exception:
        pass
    
    return False


def get_platform_type() -> PlatformType:
    """
    Determine the current platform type.
    
    Returns:
        Platform type identifier
    """
    # Check for Android first (before Linux, since Android reports as Linux)
    if detect_android():
        return "android"
    
    system = sys.platform.lower()
    
    if system.startswith('win'):
        return "windows"
    elif system.startswith('linux'):
        return "linux"
    elif system.startswith('darwin'):
        return "macos"
    else:
        return "unknown"


def get_platform_info() -> PlatformInfo:
    """
    Get comprehensive platform information.
    
    Returns:
        PlatformInfo object with detailed platform data
    """
    platform_type = get_platform_type()
    is_android = platform_type == "android"
    is_termux = detect_termux()
    
    return PlatformInfo(
        platform_type=platform_type,
        is_termux=is_termux,
        is_android=is_android,
        is_windows=platform_type == "windows",
        is_linux=platform_type == "linux",
        is_macos=platform_type == "macos",
        system=platform.system(),
        python_version=sys.version,
        architecture=platform.machine()
    )


def is_android() -> bool:
    """
    Quick check if running on Android.
    
    Returns:
        True if running on Android
    """
    return get_platform_type() == "android"


def is_windows() -> bool:
    """
    Quick check if running on Windows.
    
    Returns:
        True if running on Windows
    """
    return get_platform_type() == "windows"
