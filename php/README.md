# Šablony pro IPP projekt – PHP

## Instalace PHP a správce balíčků Composer

Pro vývoj na vašem stroji si musíte nejprve nainstalovat do systému PHP interpret. Následujte
instrukce na [webu PHP](https://www.php.net/downloads.php?usage=cli).

Správce balíčků Composer je nejjednodušší nainstalovat lokálně přímo do vašeho projektu. Následujte
instrukce na [webu nástroje Composer](https://getcomposer.org/download/). Provedení tam uvedených
příkazů povede k tomu, že se vám ve složce s projektem objeví soubor `composer.phar`. Závislosti
je poté možné nainstalovat spuštěním v PHP:

```sh
php composer.phar install
```

Tento příkaz vytvoří složku `vendor`, ve které budou balíčky nainstalovány.