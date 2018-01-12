:Author: Nitin Kumar <nitinkr@pjuniper.net>

Table & View
============

Tutorial page for PyEZ table and view

|

Table & View for Structured output
----------------------------------

`Understanding Junos PyEZ Tables and Views for structured (xml) output
<https://www.juniper.net/documentation/en_US/junos-pyez/topics/concept/junos-pyez-tables-and-views-overview.html>`_

|
|

Table & View for UnStructured output
------------------------------------

PyEZ table/view is extended to parse unstructured data. for example VTY commands
and CLI output for which we don't have structured (xml) output and convert them
to JSON.

Table Keywords
--------------

.. table:: YAML definition to fetch command output from Junos device.
   :widths: auto

   ======================    =============================================================
   Parameter                 Description
   ======================    =============================================================
   :ref:`table-name`         User-defined Table identifier.
   :ref:`table-command`      CLI/VTY command to be executed.
   :ref:`table-target`       (Optional) If the command is vty, provide the targeted fpc.
   :ref:`table-args`         (Optional) Commmand can be a jinja template. args takes key/value pair,
                             value associated with a given key is used to render command template.
   :ref:`table-key`          (Optional) Defines key to be used while forming JSON.
   :ref:`table-key-items`    (Optional) Only get the data for given keys in this list.
   :ref:`table-item`         (Optional) This is used to split whole data in different sections which
                             become the iterable reference for the associated View.

                             If item is '*', parsing is done on whole string blob and not on each line.

                             Item can also be regular expression, where regular expression is used to get key.
   :ref:`table-title`        (Optional) Title help in defining from which section the data should be parsed.
   :ref:`table-delimiter`    (Optional) delimiter to be used to split data of each line and store them as key
                             value pair in the dictionary.
   :ref:`table-view`         (Optional) View that is used to extract field data from the Table items.
   ======================    =============================================================

.. _table-name:

Table name
^^^^^^^^^^

The Table name is a user-defined identifier for the Table. The YAML file or
string can contain one or more Tables. The start of the YAML document must be
left justified. For example::

   ---
   FPCMemory:
       command: show memory

.. _table-command:

command
^^^^^^^

Command to be executed on CLI or VTY::

   # CLI command
   ---
   EthernetSwitchStatistics:
       command: show chassis ethernet-switch statistics

   # VTY command to be exectued on target FPC1
   ---
   CMErrorTable:
     command: show cmerror module brief
     target: fpc1

.. _table-target:

target
^^^^^^

Target FPC on which given command is to get executed::

   # VTY command to be exectued on target FPC1
   ---
   FPCMemory:
       command: show memory
       target: fpc1

Given FPC target in Table can be overridden through get API::

   from jnpr.junos.command.fpcmemory import FPCMemory

   stats = FPCMemory(dev)
   stats = stats.get(target='fpc2')

.. _table-args:

args
^^^^

CLI/VTY command can take parameter(s). Variable parameters in the command can be
Jinja template, dictionary under args is used to render command template::

   ---
   XMChipIfdListTable:
     command: show xmchip {{ XM_instance }} ifd list {{ direction }}
     target: fpc1
     args:
       XM_instance: 0
       direction: 0


.. _table-key:

key
^^^^

The optional key property is a tag or tags that are used to uniquely identify a
Table::

   # Value of task_name key will be taken from the dictionary created from view
   ---
   TaskIOTable:
     command: show task io
     key: task_name
     view: TaskIOView

   TaskIOView:
     columns:
       task_name: Task Name
       reads: Reads
       writes: Writes
       rcvd: Rcvd
       sent: Sent
       dropped: Dropped


   # Key can be a list also
   ---
   FPCIPV4AddressTable:
     command: show ipv4 address
     target: fpc1
     key:
       - name
       - addr
     view: FPCIPV4AddressView

   FPCIPV4AddressView:
     columns:
       index: Index
       addr: Address
       name: Name

.. _table-key-items:

key_items
^^^^^^^^^

The optional key_items property is used to select only certain key data in JSON::

   ---
   FPCMemory:
       command: show memory
       target: fpc1
       key: ID
       key_items:
         - 1
         - 2
       view: FPCMemoryView

   FPCMemoryView:
       columns:
           id: ID
           base: Base
           total: Total(b)
           free: Free(b)
           used: Used(b)
           perc: "%"
           name: Name

Output for **show memory** is::

   ID        Base      Total(b)       Free(b)       Used(b)   %   Name
   --  ----------   -----------   -----------   -----------  ---   -----------
   0    4d9ad8e8    1726292636    1514622708     211669928   12  Kernel
   1    b47ffb88      67108860      53057404      14051456   20  LAN buffer
   2    bcdfffe0      52428784      52428784             0    0  Blob
   3    b87ffb88      73400316      73400316             0    0  ISSU scratch

Even though we have four ID row here, data returned will be for just 1 & 2 as
provided in key_items::

   {1: {'base': 'b47ffb88',
        'free': 53057404,
        'id': 1,
        'name': 'LAN buffer',
        'perc': 20,
        'total': 67108860,
        'used': 14051456},
    2: {'base': 'bcdfffe0',
        'free': 52428784,
        'id': 2,
        'name': 'Blob',
        'perc': 0,
        'total': 52428784,
        'used': 0}}

.. _table-item:

item
^^^^
The item value is a string or regular expression to split the output in sections.

Say the out of the command **show devices local** is::

   TSEC Ethernet Device Driver: .le1, Control 0x4296c218, (1000Mbit)
   HW reg base 0xff724000
     [0]: TxBD base 0x7853ce20, RxBD Base 0x7853d640
     [1]: TxBD base 0x7853d860, RxBD Base 0x7853e080
     [2]: TxBD base 0x7853e2a0, RxBD Base 0x785422c0
     [3]: TxBD base 0x785426e0, RxBD Base 0x78544700
   Receive:
     185584608 bytes, 2250212 packets, 0 FCS errors, 0 multicast packets
     107271 broadcast packets, 0 control frame packets
     0 PAUSE frame packets, 0 unknown OP codes
     0 alignment errors, 0 frame length errors
     0 code errors, 0 carrier sense errors
     0 undersize packets, 0 oversize packets
     0 fragments, 0 jabbers, 0 drops
   Receive per queue:
     [0]: 0 bytes, 0 packets, 0 dropped
           0 jumbo, 0 truncated jumbo
     [1]: 0 bytes, 0 packets, 0 dropped
           0 jumbo, 0 truncated jumbo
     [2]: 0 bytes, 0 packets, 0 dropped
           0 jumbo, 0 truncated jumbo
     [3]: 203586808 bytes, 2250219 packets, 0 dropped
           0 jumbo, 0 truncated jumbo
   Transmit:
     288184646 bytes, 2038370 packets, 0 multicast packets
     106531 broadcast packets, 0 PAUSE control frames
     0 deferral packets, 0 excessive deferral packets
     0 single collision packets, 0 multiple collision packets
     0 late collision packets, 0 excessive collision packets
     0 total collisions, 0 drop frames, 0 jabber frames
     0 FCS errors, 0 control frames, 0 oversize frames
     0 undersize frames, 0 fragments frames
   Transmit per queue:
     [0]:   10300254 bytes,        72537 packets
                   0 dropped,          0 fifo errors
     [1]:    4474302 bytes,       106531 packets
                   0 dropped,          0 fifo errors
     [2]:  260203538 bytes,      1857137 packets
                   0 dropped,          0 fifo errors
     [3]:     199334 bytes,         2179 packets
                   0 dropped,          0 fifo errors
   TSEC status counters:
   kernel_dropped:0, rx_large:0 rx_short: 0
   rx_nonoctet: 0, rx_crcerr: 0, rx_overrun: 0
   rx_bsy: 0,rx_babr:0, rx_trunc: 0
   rx_length_errors: 0, rx_frame_errors: 0 rx_crc_errors: 0
   rx_errors: 0, rx_ints: 2250110, collisions: 0
   eberr:0, tx_babt: 0, tx_underrun: 0
   tx_timeout: 0, tx_timeout: 0,tx_window_errors: 0
   tx_aborted_errors: 0, tx_ints: 2038385, resets: 1


   TSEC Ethernet Device Driver: .le3, Control 0x42979220, (1000Mbit)
   HW reg base 0xff726000
     [0]: TxBD base 0x78545720, RxBD Base 0x78545f40
     [1]: TxBD base 0x78546160, RxBD Base 0x78546980
     [2]: TxBD base 0x78546ba0, RxBD Base 0x7854abc0
     [3]: TxBD base 0x7854afe0, RxBD Base 0x7854d000
   Receive:
     0 bytes, 0 packets, 0 FCS errors, 0 multicast packets
     0 broadcast packets, 0 control frame packets
     0 PAUSE frame packets, 0 unknown OP codes
     0 alignment errors, 0 frame length errors
     0 code errors, 0 carrier sense errors
     0 undersize packets, 0 oversize packets
     0 fragments, 0 jabbers, 0 drops
   Receive per queue:
     [0]: 0 bytes, 0 packets, 0 dropped
           0 jumbo, 0 truncated jumbo
     [1]: 0 bytes, 0 packets, 0 dropped
           0 jumbo, 0 truncated jumbo
     [2]: 0 bytes, 0 packets, 0 dropped
           0 jumbo, 0 truncated jumbo
     [3]: 0 bytes, 0 packets, 0 dropped
           0 jumbo, 0 truncated jumbo
   Transmit:
     6817984 bytes, 106531 packets, 0 multicast packets
     106531 broadcast packets, 0 PAUSE control frames
     0 deferral packets, 0 excessive deferral packets
     0 single collision packets, 0 multiple collision packets
     0 late collision packets, 0 excessive collision packets
     0 total collisions, 0 drop frames, 0 jabber frames
     0 FCS errors, 0 control frames, 0 oversize frames
     0 undersize frames, 0 fragments frames
   Transmit per queue:
     [0]:          0 bytes,            0 packets
                   0 dropped,          0 fifo errors
     [1]:    4474302 bytes,       106531 packets
                   0 dropped,          0 fifo errors
     [2]:          0 bytes,            0 packets
                   0 dropped,          0 fifo errors
     [3]:          0 bytes,            0 packets
                   0 dropped,          0 fifo errors
   TSEC status counters:
   kernel_dropped:0, rx_large:0 rx_short: 0
   rx_nonoctet: 0, rx_crcerr: 0, rx_overrun: 0
   rx_bsy: 0,rx_babr:0, rx_trunc: 0
   rx_length_errors: 0, rx_frame_errors: 0 rx_crc_errors: 0
   rx_errors: 0, rx_ints: 0, collisions: 0
   eberr:0, tx_babt: 0, tx_underrun: 0
   tx_timeout: 0, tx_timeout: 0,tx_window_errors: 0
   tx_aborted_errors: 0, tx_ints: 106531, resets: 1


And the table to parse above output, item is used to split them into sections.::

   ---
   DevicesLocalTable:
     command: show devices local
     target: fpc1
     item: 'TSEC Ethernet Device Driver: (\.?\w+),'
     key: name
     view: DevicesLocalView

   DevicesLocalView:
     fields:
       TSEC_status_counters: _TSECStatusCountersTable
       receive_counters: _ReceiveTable
       transmit_per_queue: _TransmitQueueTable

`key` in above table is fetched from the regex group used in item.

**item** Can also be provided as '*' if we dont want each line matching but from
whole output.::

   _ReceiveTable:
     item: '*'
     title: 'Receive:'
     view: _ReceiveView

   _ReceiveView:
     regex:
       bytes: '(\d+) bytes'
       packets: '(\d+) packets'
       FCS_errors: '(\d+) FCS errors'
       broadcast_packets: '(\d+) broadcast packets'


.. _table-title:

title
^^^^^
Title helps in deciding the data to be parsed starting point.::

   _TSECStatusCountersTable:
     item: '*'
     title: 'TSEC status counters:'
     view: _TSECStatusCountersView

   _TSECStatusCountersView:
     regex:
       kernel_dropped: 'kernel_dropped:(\d+)'
       rx_large: 'rx_large:(\d+)'

helps to parse data from::

   TSEC status counters:
   kernel_dropped:0, rx_large:0 rx_short: 0
   rx_nonoctet: 0, rx_crcerr: 0, rx_overrun: 0
   rx_bsy: 0,rx_babr:0, rx_trunc: 0
   rx_length_errors: 0, rx_frame_errors: 0 rx_crc_errors: 0
   rx_errors: 0, rx_ints: 2250110, collisions: 0
   eberr:0, tx_babt: 0, tx_underrun: 0
   tx_timeout: 0, tx_timeout: 0,tx_window_errors: 0
   tx_aborted_errors: 0, tx_ints: 2038385, resets: 1

.. note:: In above table '*' consider whole data as one paragraph.


.. _table-delimiter:

delimiter
^^^^^^^^^

There are some command output which are just key value pairs. They can be split
using given delimiter and converted to JSON. Consider below table::

   ---
   FPCLinkStatTable:
       command: show link stats
       target: fpc1
       delimiter: ":"

Output for command **show links stats**::

   PPP LCP/NCP: 0
   HDLC keepalives: 0
   RSVP: 0
   ISIS: 0
   OSPF Hello: 539156
   OAM:  0
   BFD:  15
   UBFD:  0
   LMI:  0
   LACP: 0
   ETHOAM: 0
   SYNCE:  0
   PTP:  0
   L2TP:  0
   LNS-PPP:  0
   ARP:  4292
   ELMI:  0
   VXLAN MRESOLVE: 0
   Unknown protocol: 42

Using given delimiter ":" output is parsed to get::

   {'ARP': 4292, 'ELMI': 0, 'SYNCE': 0, 'ISIS': 0, 'BFD': 15, 'PPP LCP/NCP': 0,
   'OAM': 0, 'ETHOAM': 0, 'LACP': 0, 'LMI': 0, 'Unknown protocol': 42,
   'UBFD': 0, 'L2TP': 0, 'HDLC keepalives': 0, 'LNS-PPP': 0,
   'OSPF Hello': 539156, 'RSVP': 0, 'VXLAN MRESOLVE': 0, 'PTP': 0}


.. _table-view:

view
^^^^^

View is defined how the output from the table to be parsed. Different keyword
which can be used with view is defined in next section. Every view will be
associated with a table.

Example::

   ---
   CMErrorTable:
     command: show cmerror module brief
     target: fpc1
     key: module
     view: CMErrorView

   CMErrorView:
     columns:
       module: Module
       name: Name
       errors: Active Errors

View Keywords
-------------

Junos PyEZ Tables select specific data from the command reply from devices running Junos OS.
A Table is associated with a View, which is used to access fields in the Table items.
You associate a Table with a particular View by including the view property in the Table
definition, which takes the View name as its argument.

A View maps your user-defined field names to string elements in the selected Table
items. A View enables you to access specific fields in the output as variables
with properties that can be manipulated in Python. Junos PyEZ handles the extraction
of the data into JSON for unstructured command output.

.. table:: YAML definition to parse command output
   :widths: auto

   ====================    =============================================================
   Parameter               Description
   ====================    =============================================================
   :ref:`table-columns`    (Optional) List of column title as seen in command output
   :ref:`table-filters`    (Optional) list of column item which should only go to dictionary data.
   ====================    =============================================================

.. _table-columns:

columns
^^^^^^^

Consider the case where the output of the command is in row/column format. For
Example **show lkup-asic wedge-client**::

   Wedge poll thread state  : 'Started'
   Total registered clients : 4
   CID         Name PfeInst AscIdx            PPEMask   ZoneMask  RordChk     Mode
   ----------------------------------------------------------------------------------
     0    LUCHIP(0)       0      0 0x0000000000000000 0x000000000000ffff 0x0000f000 Disabled   NORMAL
     1    LUCHIP(4)       0      1 0x0000000000000000 0x000000000000ffff 0x0000f000 Disabled   NORMAL
     2    LUCHIP(8)       0      2 0x0000000000000000 0x000000000000ffff 0x0000f000 Disabled   NORMAL
     3   LUCHIP(12)       0      3 0x0000000000000000 0x000000000000ffff 0x0000f000 Disabled   NORMAL

   Client ID       Curr State    Prev State   Last read
   ------------------------------------------------------
       0              NORMAL        NORMAL     6294337620
       1            DISABLED        NORMAL     6294337620
       2            DISABLED        NORMAL     6294337620
       3            DISABLED        NORMAL     6294337620

And we want to parse the data of second section consisting of client id, curr state,
previous state and last read. We will define table/view with view declares all columns::

   ---
   LUChipStatusTable:
     command: show lkup-asic wedge-client
     target: fpc1
     key: Client ID
     view: LUChipStatusView

   LUChipStatusView:
     columns:
       client_id: Client ID
       curr_state: Curr State
       prev_state: Prev State
       last_read: Last read

Output received will be::

   {0: {'client_id': 0,
        'curr_state': 'NORMAL',
        'last_read': 6294337620,
        'prev_state': 'NORMAL'},
    1: {'client_id': 1,
        'curr_state': 'DISABLED',
        'last_read': 6294337620,
        'prev_state': 'NORMAL'},
    2: {'client_id': 2,
        'curr_state': 'DISABLED',
        'last_read': 6294337620,
        'prev_state': 'NORMAL'},
    3: {'client_id': 3,
        'curr_state': 'DISABLED',
        'last_read': 6294337620,
        'prev_state': 'NORMAL'}}

.. note:: In columns we need to provide all column title to help parse the data.

.. _table-filters:

filters
^^^^^^^

Consider below table/view::

   ---
   CMErrorTable:
     command: show cmerror module brief
     target: fpc1
     key:
       - module
     view: CMErrorView

   CMErrorView:
     columns:
       module: Module
       name: Name
       errors: Active Errors
     filters:
       - errors

Output from command **show cmerror module brief**::

   ---------------------------------------
   Module  Name              Active Errors
   ---------------------------------------
   1       PQ3 Chip          0
   2       Host Loopback     0
   3       CM[0]             0
   4       LUCHIP(0)         0
   5       TOE-LU-0:0:0      0
   6       LUCHIP(4)         0
   7       TOE-LU-0:1:0      0
   8       LUCHIP(8)         0
   9       TOE-LU-0:2:0      0
   10      LUCHIP(12)        0
   11      TOE-LU-0:3:0      0
   12      XMCHIP(0)         0
   13      TOE-XM-0:0:0      0
   14      MPC               0
   15      GE Switch         0
   16      PMB               0
   17      JNH               0
   18      PRECL:0:XM:0      0
   19      PRECL:1:XM:0      0


Output::

   {1: {'errors': 0}, 2: {'errors': 0}, 3: {'errors': 0}, 4: {'errors': 0},
   5: {'errors': 0}, 6: {'errors': 0}, 7: {'errors': 0}, 8: {'errors': 0},
   9: {'errors': 0}, 10: {'errors': 0}, 11: {'errors': 0}, 12: {'errors': 0},
   13: {'errors': 0}, 14: {'errors': 0}, 15: {'errors': 0}, 16: {'errors': 0},
   17: {'errors': 0}, 18: {'errors': 0}, 19: {'errors': 0}}