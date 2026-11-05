from .otomoto import OtomotoParser

# OLX is added here once access is confirmed (it currently answers 403 from CloudFront).
PARSERS = {"otomoto": OtomotoParser()}
