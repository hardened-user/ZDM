ZDM - Zabbix Data Mining
================

EN:

A set of scripts and templates for data mining in Zabbix


RU:

Набор скриптов и шаблонов для сбора данных в Zabbix


Requirements for the Zabbix Server host
----------------
* zabbix server 4.0


Requirements for the Zabbix Agent host
----------------
* python 3.x
* python-memcached
* memcached


Ansible example
----------------
    ansible-playbook example.yml
    ansible-playbook example.yml --tags=zdm



Modules
----------------
* memcached
* iostat
