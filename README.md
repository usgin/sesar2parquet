# SESAR2

Revamped SESAR application.

## Description

SESAR operates the registry that distributes the International Geo Sample Number IGSN. SESAR catalogs and preserves sample metadata profiles, and provides access to the sample catalog via the Global Sample Search.

The repository contains code for the frontend application as well as back-end Apis.

## Getting Started

## Testing

When running Django Tests, use the test_settings.py file in order to test on unmanaged models. You can do so by running the following: `python manage.py test --settings sesar.test_settings`

### Dependencies

* Django 5.0.6