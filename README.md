# PSLRegex

This repo provides a Jupyter Notebook that fetches the last IANA and Public Suffix List data files, merging them into a unique database of TLD and suffixes with genereal information.

## To ignore

I would ignore `country-code`, `generic`, `generic-restrictec`, `infrastructure`.

Then I would delete this also by the suffixes, for example:

> amazon.com -> amazon

because .com belongs to `generic` eTLDs.

In that way:
> `load.s3.amazonaws.com` -> `load.s3.amazonaws`
instead of:
> `load.s3.amazonaws.com` -> `load`


# IMPORTANT!

`Type` and `Tld Type` only differs when `Type` is `private-domains`.

That means that the not-`private-domains` type will always be like the tld.

```tlds = psl.etldFrame#[psl.etldFrame.l == 0]

display(tlds[tlds.type != tlds['tld type']].drop_duplicates(subset=['type','origin', 'tld type', 'suffix type']))

display(tlds.drop_duplicates(subset=['type','origin']))
```

All the multiple level `cc` have the tld?