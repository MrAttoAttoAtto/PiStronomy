from rational_gui import lockedScreen, verificationScreen, fingerprintScreen, hudScreen, dispenseScreen, adminScreen, refillScreen

__all__ = [
    'controller',
    'hudScreen',
    'lockedScreen',
    'verificationScreen',
    'adminScreen',
    'dispenseScreen',
    'fingerprintScreen',
    'hudScreen'
]

pages = [
    lockedScreen.LockedScreen,
    verificationScreen.VerificationScreen,
    fingerprintScreen.FingerprintScreen,
    hudScreen.HudScreen,
    dispenseScreen.DispenseScreen,
    adminScreen.AdminScreen,
    refillScreen.RefillScreen
]