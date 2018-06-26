:Author: Nitin Kumar <nitinkr@pjuniper.net>

************
Table & View
************

Tutorial page for PyEZ table and view

|

Table & View for Structured output
##################################

`Understanding Junos PyEZ Tables and Views for structured (xml) output
<https://www.juniper.net/documentation/en_US/junos-pyez/topics/concept/junos-pyez-tables-and-views-overview.html>`_

|

Table & View for UnStructured output
####################################

PyEZ table/view is extended to parse unstructured data. for example VTY commands
and CLI output for which we don't have structured (xml) output and convert them
to JSON.

Table Keywords
==============

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
   :ref:`table-eval`         (Optional) Mathematical expression which can be evaluated using python eval
                             function. This can be used on `data` dictionary which is returned by table
                             view.                          
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

.. _table-eval:

eval
^^^^

Using eval keyword, we can add extra key/value to the final data returned from Table/View.
value is evaluated from the Mathematical expression provided by the user.
eval expression can use **data** which can be considered as the dictionary returned from
table/view. data should be kept under Jinja template so that PyEZ can replace data with 
dictonary.


.. note:: For more details about python eval function. check this `Link <https://docs.python.org/3/library/functions.html#eval>`_

Examples::

    ---
    CChipLiInterruptStatsTable:
      command: show mqss {{ chip_instance }} li interrupt-stats
      target: NULL
      args:
        chip_instance: 0
      key:
        - li_block
        - name
      view: CChipLiInterruptStatsView
      eval:
        cchip_errors_from_lkup_chip: "reduce(lambda x,y: x+y, [v['interrupts'] for k,v in {{ data }}.items()])"

    CChipLiInterruptStatsView:
      columns:
        li_block: LI Block
        name: Interrupt Name
        interrupts: Number of Interrupts
        last_occurance: Last Occurrence

|

::

    ---
    CChipLiInterruptStatsTable:
      command: show xmchip {{ chip_instance }} li interrupt-stats
      target: NULL 
      args:
        chip_instance: 0
      key:
        - li_block
        - name
      eval:
        cchip_errors_from_lkup_chip: "reduce(lambda x,y: x+y, [v['interrupts'] for k,v in {{ data }}.items()])"
      view: CChipLiInterruptStatsView

    CChipLiInterruptStatsView:
      columns:
        li_block: LI Block
        name: Interrupt Name
        interrupts: Number of Interrupts
        last_occurance: Last Occurrence


eval can be used to calculate multile values::

    ---
    CChipDRDErrTable:
      command: show mqss {{ instance }} drd error-stats
      args:
        instance: 0
      target: NULL 
      key: Interrupt Name
      item: '*'
      view: CChipDRDErrView
      eval:
        cchip_drd_wan_errors: sum([v['interrupt_count_wan'] for k, v in {{ data }}.items() if isinstance(v, dict)])
        cchip_drd_fab_errors: sum([v['interrupt_count_fab'] for k, v in {{ data }}.items() if isinstance(v, dict)])

    CChipDRDErrView:
      regex:
        cchip_drd_wan_timeouts: 'Total WAN reorder ID timeout errors:\s+(\d+)'
        cchip_drd_fab_timeouts: 'Total fabric reorder ID timeout errors:\s+(\d+)'
      columns:
        interrupt_name: Interrupt Name
        interrupt_count_wan: 
          -         Number of
          - Reorder Engine 0
        interrupt_count_fab:
          - Interrupts
          -   Reorder Engine 1

|

::

    ---
    CChipDRDErrTable:
      command: show xmchip {{ instance }} drd error-stats
      args:
        instance: 0
      target: NULL 
      key: Interrupt Name
      item: '*'
      view: CChipDRDErrView
      eval:
        cchip_drd_wan_errors: sum([v['interrupt_count'] for k, v in {{ data }}.items() if k.endswith('_0')])
        cchip_drd_fab_errors: sum([v['interrupt_count'] for k, v in {{ data }}.items() if k.endswith('_1')])
        
    CChipDRDErrView:
      regex:
        cchip_drd_wan_timeouts: 'Total WAN reorder ID timeout errors:\s+(\d+)'
        cchip_drd_fab_timeouts: 'Total fabric reorder ID timeout errors:\s+(\d+)'
      columns:
        interrupt_name: Interrupt Name
        interrupt_count: Number of Interrupts
      filters:
        - interrupt_count


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
=============

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
   :ref:`view-columns`     (Optional) List of column title as seen in command output
   :ref:`view-regex`       (Optional) List of regular expression to match desired content
   :ref:`view-fields`      (Optional) List of nested tables.
   :ref:`view-exists`      (Optional) If the given statement exists, sets True else False
   :ref:`view-filters`     (Optional) list of column item which should only go to dictionary data
   ====================    =============================================================



.. _view-columns:

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


There are situation when column title are spread across multiple line. In such 
cases columns keys element should be list of words corresponding to their columns.

For command ``show cmerror module brief`` with cli output::

  -------------------------------------------------------------------------
  Module  Name              Active Errors  PFE       Callback    ModuleData
                                          Specific  Function              
  -------------------------------------------------------------------------
  1       PQ3 Chip          0              Yes       0x00000000  0x00000000
  2       Host Loopback     0              No        0x00000000  0x464295b0
  3       CM[0]             0              No        0x41f550f0  0x462f767c


Table/View to parse above output::

  ---
  CMErrorTable:
    command: show cmerror module brief dummy multiline
    target: Null
    key: module
    view: CMErrorView

  CMErrorView:
    columns:
      module: Module
      name: Name
      errors: Active Errors
      pfe:
        - PFE
        - Specific
      callback:
        - Callback
        - Function
      data: ModuleData

Similarly for command ``show mqss 0 fi interrupt-stats`` with cli output::

  FI interrupt statistics
  -----------------------

  --------------------------------------------------------------------------------------
  Stream  Total RLIM  Total       Cell timeout  Total Reorder  Total cell   Total number
          request     PT/MALLOC   Ignored       cell timeout   drops in     of times
          counter     Usemeter                  errors         secure mode  entered into
          saturation  Drops                                                 secure mode
  --------------------------------------------------------------------------------------
  36      0           0           1             1              0            0
  128     0           0           1             49             0            0
  142     0           0           1             53             0            0
  --------------------------------------------------------------------------------------
  --------------------------------------------------------------------------
  Stream  Stream reconfiguration  Total Error  Total Late  Total CRC Errored
          count due to pointers   Cells        Cells       Packets
          stalled in secure mode
  --------------------------------------------------------------------------
  36      0                       0            1           0
  --------------------------------------------------------------------------

Table/View to parse above output::

  CChipFiStatsTable:
    command: show mqss {{ chip_instance }} fi interrupt-stats
    target: fpc8
    args:
      chip_instance: 0
    key: Stream
    view: CChipFiStatsView

  CChipFiStatsView:
    columns:
      stream: Stream
      req_sat:
        - Total RLIM
        - request
        - counter
        - saturation
      cchip_fi_malloc_drops:
        - Total
        - PT/MALLOC
        - Usemeter
        - Drops
      cell_timeout_ignored:
        - Cell timeout
        - Ignored
      cchip_fi_cell_timeout:
        - Total Reorder
        - cell timeout
        - errors
      drops_in_secure:
        - Total cell
        - drops in
        - secure mode
      times_in_secure:
        - Total number
        - of times
        - entered into
        - secure mode


.. _view-regex:

regex
^^^^^
list of regular expression which combined together should match one line.
consider command output for ``show icmp statistics``

::

    ICMP Statistics:
              0 requests
              0 throttled
              0 network unreachables
              0 ttl expired
              0 redirects
              0 mtu exceeded
              0 source route denials
              0 filter prohibited
              0 other unreachables
              0 parameter problems
              0 ttl captured
              0 icmp/option handoffs
              0 igmp v1 handoffs
              0 tag te requests
              0 tag te to RE

    ICMP Errors:
              0 unknown unreachables
              0 unsupported ICMP type
              0 unprocessed redirects
              0 invalid ICMP type
              0 invalid protocol
              0 bad input interface
              0 bad route lookup
              0 bad nh lookup
              0 bad cf mtu
              0 runts

    ICMP Discards:
              0 multicasts
              0 bad source addresses
              0 bad dest addresses
              0 IP fragments
              0 ICMP errors
              0 unknown originators

    ICMP Debug Messages:
              0 throttled

    ICMP Rate Limit Settings:
            500 pps per iff
            1000 pps total

Here datas are under different title and data is numbers + word(s).
Hence the below table/view use regular expression to parse key (numbers)
and value (words). 

Table/View::

    ---
    ICMPStatsTable:
      command: show icmp statistics
      target: fpc1
      view: ICMPStatsView

    ICMPStatsView:
      fields:
        discards: _ICMPDiscardsTable
        errors: _ICMPErrorsTable
        rate: _ICMPRateTable

    _ICMPDiscardsTable:
      title: ICMP Discards
      key: name
      view: _ICMPDiscardsView

    _ICMPDiscardsView:
      regex:
        value: \d+
        name: '(\w+(\s\w+)*)'

    _ICMPErrorsTable:
      title: ICMP Errors
      key: name
      view: _ICMPErrorsView

    _ICMPErrorsView:
      regex:
        error: numbers
        name: words

    _ICMPRateTable:
      title: ICMP Rate Limit Settings
      key: name
      view: _ICMPRateView

    _ICMPRateView:
      regex:
        rate: numbers
        name: words

Check _ICMPDiscardsTable and _ICMPDiscardsView. *title* (ICMP Discards) under 
_ICMPDiscardsTable is used to get to the starting point for parsing.
value and name are the keys and corresponding regex value is combined to parse
each line. Also in such data key cannot be value, so we can select right hand 
side data *name* as the key. 

We also define some inbuilt keywords which can be used in place of regular
expression. Check _ICMPErrorsView. Below are the list of inbuilt keywords and 
corresponding expression used.

* **numbers** = (pp.Word(pp.nums) + pp.Optional(pp.Literal('.') + pp.Word(pp.nums))).setParseAction(lambda i: ''.join(i))
* **hex_numbers** = pp.OneOrMore(pp.Word(pp.nums, min=1)) & pp.OneOrMore(pp.Word('abcdefABCDEF', min=1))
* **word** = pp.Word(pp.alphanums) | pp.Word(pp.alphas)
* **words** = (pp.OneOrMore(word)).setParseAction(lambda i: ' '.join(i))
* **percentage** = pp.Word(pp.nums) + pp.Literal('%')
* **printables** = pp.OneOrMore(pp.Word(pp.printables))

Here **pp** is coming from (import pyparsing as pp)

When table :ref:`table-item` is proved, regex is used on the splitted items.
Say when item is * regex is used on whole string blob and not combined to parse
each line. For example check the output of command ``show ithrottle id 0``::

    SENT: Ukern command: show ithrottle id 0

    ID  Usage %  Cfg State  Oper State     Name
    --  -------  ---------  ----------   --------
      0     50.0       1           1      TOE ithrottle

    Throttle Times:             In hptime ticks     In ms
                                ---------------     ------
      Timer Interval                     333333     5.000
      Allowed time                       166666     2.500
      Allowed excess                       8333     0.125
      Start time                      488655082     n/a
      Run time this interval                  0     0.000
      Deficit                                 0     0.000
      Run time max                        17712     0.266
      Run time total               144154525761     2162317

    Min Usage Perc:    25.0
    Max Usage Perc:    50.0
    AdjustUsageEnable: 1

    Throttle Stats:
      Starts    : 65708652
      Stops     : 65708652
      Checks    : 124149442
      Enables   : 0
      Disables  : 0
      AdjUp     : 6
      AdjDown   : 4

Table/View used for parsing above output::

    IthrottleIDTable:
      command: show ithrottle id {{ id }}
      args:
        id: 0
      item: '*'
      target: fpc1
      view: IthrottleIDView

    IthrottleIDView:
      regex:
        min_usage: 'Min Usage Perc:    (\d+\.\d+)'
        max_usage: 'Max Usage Perc:    (\d+\.\d+)'
        usg_enable: 'AdjustUsageEnable: (\d)'
      fields:
        throttle_stats: _ThrottleStatsTable

    _ThrottleStatsTable:
        title: Throttle Stats
        delimiter: ":"

Here item is \*, hence whole string blob is used to search for given regular expressions.

output::

    {'max_usage': 50.0,
    'min_usage': 25.0,
    'throttle_stats': {'AdjDown': 4,
                        'AdjUp': 6,
                        'Checks': 124149442,
                        'Disables': 0,
                        'Enables': 0,
                        'Starts': 65708652,
                        'Stops': 65708652},
    'usg_enable': 1}

.. note:: grouping is used to get specific data from regex expression. For example. (\d+\.\d+) is used to get the float value from string search expression. if we change expression to **Max Usage Perc:    (\d+)\.\d+** we will get integer part only.


.. _view-fields:

fields
^^^^^^

Where the command output has different sections of data which need different logic
to parse those subset of data, we can define nested tables under fields section.

For command ``show xmchip 0 pt stats`` we have 2 section of data::

        SENT: Ukern command: show xmchip 0 pt stats


        WAN PT statistics (Index 0)
        ---------------------------

        PCT entries used by all WI-1 streams         : 0
        PCT entries used by all WI-0 streams         : 0
        PCT entries used by all LI streams           : 0
        CPT entries used by all multicast packets    : 0
        CPT entries used by all WI-1 streams         : 0
        CPT entries used by all WI-0 streams         : 0
        CPT entries used by all LI streams           : 0

        Fabric PT statistics (Index 1)
        ------------------------------

        PCT entries used by all FI streams           : 0
        PCT entries used by all WI (Unused) streams  : 0
        PCT entries used by all LI streams           : 0
        CPT entries used by all multicast packets    : 0
        CPT entries used by all FI streams           : 0
        CPT entries used by all WI (Unused) streams  : 0
        CPT entries used by all LI streams           : 0

So we defined fields with two nested table each used to parse different subset
of data::

        ---
        XMChipStatsTable:
          command: show xmchip 0 pt stats
          target: fpc1
          view: XMChipStatsView

        XMChipStatsView:
          fields:
            wan_pt_stats: _WANPTStatTable
            fabric_pt_stats: _FabricPTStatTable

        _WANPTStatTable:
          title: WAN PT statistics (Index 0)
          delimiter: ":"

        _FabricPTStatTable:
          title: Fabric PT statistics (Index 1)
          delimiter: ":"

Output::

  {'fabric_pt_stats': {'CPT entries used by all FI streams': 0,
                      'CPT entries used by all LI streams': 0,
                      'CPT entries used by all WI (Unused) streams': 0,
                      'CPT entries used by all multicast packets': 0,
                      'PCT entries used by all FI streams': 0,
                      'PCT entries used by all LI streams': 0,
                      'PCT entries used by all WI (Unused) streams': 0},
  'wan_pt_stats': {'CPT entries used by all LI streams': 0,
                    'CPT entries used by all WI-0 streams': 0,
                    'CPT entries used by all WI-1 streams': 0,
                    'CPT entries used by all multicast packets': 0,
                    'PCT entries used by all LI streams': 0,
                    'PCT entries used by all WI-0 streams': 0,
                    'PCT entries used by all WI-1 streams': 0}}

Another example using command output for ``show ttp statistics``::

    SENT: Ukern command: show ttp statistics

    TTP Statistics:
                       Receive    Transmit
                    ----------  ----------
     L2 Packets           4292     1093544
     L3 Packets         542638           0
     Drops                   0           0
     Netwk Fail              0           0
     Queue Drops             0           0
     Unknown                 0           0
     Coalesce                0           0
     Coalesce Fail           0           0

    TTP Transmit Statistics:
                       Queue 0     Queue 1     Queue 2    Queue 3
                    ----------  ----------  ----------  ----------
     L2 Packets        1093544           0           0           0
     L3 Packets              0           0           0           0

    TTP Receive Statistics:
                       Control        High      Medium         Low     Discard
                    ----------  ----------  ----------  ----------  ----------
     L2 Packets              0           0        4292           0           0
     L3 Packets              0      539172        3466           0           0
     Drops                   0           0           0           0           0
     Queue Drops             0           0           0           0           0
     Unknown                 0           0           0           0           0
     Coalesce                0           0           0           0           0
     Coalesce Fail           0           0           0           0           0

    TTP Receive Queue Sizes:
     Control Plane : 0 (max is 4473)
     High          : 0 (max is 4473)
     Medium        : 0 (max is 4473)
     Low           : 0 (max is 2236)

    TTP Transmit Queue Size: 0 (max is 6710)

Table/View used to parse above output using nested table/view under fields::

    ---
    FPCTTPStatsTable:
      command: show ttp statistics
      target: fpc2
      view: FPCTTPStatsView

    FPCTTPStatsView:
      fields:
        TTPStatistics: _FPCTTPStatisticsTable
        TTPTransmitStatistics: _FPCTTPTransmitStatisticsTable
        TTPReceiveStatistics: _FPCTTPReceiveStatisticsTable
        TTPQueueSizes: _FPCTTPQueueSizesTable

    _FPCTTPStatisticsTable:
      title: TTP Statistics
      view: _FPCTTPStatisticsView

    _FPCTTPStatisticsView:
      columns:
        rcvd: Receive
        tras: Transmit

    _FPCTTPTransmitStatisticsTable:
      title: TTP Transmit Statistics
      view: _FPCTTPTransmitStatisticsView

    _FPCTTPTransmitStatisticsView:
      columns:
        queue0: Queue 0
        queue1: Queue 1
        queue2: Queue 2
        queue3: Queue 3
      filters:
        - queue2

    _FPCTTPReceiveStatisticsTable:
      title: TTP Receive Statistics
      key: name
      key_items:
        - Coalesce
      view: _FPCTTPReceiveStatisticsView

    _FPCTTPReceiveStatisticsView:
      columns:
        control: Control
        high: High
        medium: Medium
        low: Low
        discard: Discard

    _FPCTTPQueueSizesTable:
      title: TTP Receive Queue Sizes
      delimiter: ":"

Output::

    {'TTPQueueSizes': {'Control Plane': '0 (max is 4473)',
                       'High': '0 (max is 4473)',
                       'Low': '0 (max is 2236)',
                       'Medium': '0 (max is 4473)'},
     'TTPReceiveStatistics': {'Coalesce': {'control': 0,
                                           'discard': 0,
                                           'high': 0,
                                           'low': 0,
                                           'medium': 0,
                                           'name': 'Coalesce'}},
     'TTPStatistics': {'Coalesce': {'name': 'Coalesce', 'rcvd': 0, 'tras': 0},
                       'Coalesce Fail': {'name': 'Coalesce Fail',
                                         'rcvd': 0,
                                         'tras': 0},
                       'Drops': {'name': 'Drops', 'rcvd': 0, 'tras': 0},
                       'L2 Packets': {'name': 'L2 Packets',
                                      'rcvd': 0,
                                      'tras': 7468},
                       'L3 Packets': {'name': 'L3 Packets', 'rcvd': 0, 'tras': 0},
                       'Netwk Fail': {'name': 'Netwk Fail',
                                      'rcvd': 0,
                                      'tras': 173},
                       'Queue Drops': {'name': 'Queue Drops',
                                       'rcvd': 0,
                                       'tras': 0},
                       'Unknown': {'name': 'Unknown', 'rcvd': 0, 'tras': 0}},
     'TTPTransmitStatistics': {'L2 Packets': {'queue2': 0},
                               'L3 Packets': {'queue2': 0}}}

.. note:: fields in unstructured table/view is different compared to rpc based table/view. For RPC, fields are xpath tags.


.. _view-exists:


exists
^^^^^^

If we just need to check if the given string statement is present or not in the
command output. we can use ``exists`` option. For example

For command output of ``show host_loopback status-summary``::

    SENT: Ukern command: show host_loopback status-summary

    Host Loopback Toolkit Status Summary:

    No detected wedges

    No toolkit errors


Table/View defined::

    ---
    HostlbStatusSummaryTable:
      command: show host_loopback status-summary
      target: fpc1
      view: HostlbStatusSummaryView

    HostlbStatusSummaryView:
      exists:
        no_detected_wedges: No detected wedges
        no_toolkit_errors: No toolkit errors

Output::

    {'no_detected_wedges': True, 'no_toolkit_errors': True}

.. _view-filters:

filters
^^^^^^^

When we are interested in only few keys from the parsed output, we can filter
filter out the desired key/value using filters. Filters takes a list of keys
from columns items. Final output dictionary should only consist of items listed
in filters per iteration of view output.

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

Output from command ``show cmerror module brief``::

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