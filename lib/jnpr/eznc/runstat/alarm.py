from . import RunstatMaker as RSM

##### -------------------------------------------------------------------------
##### nice illustration of using the same View on different Tables
##### -------------------------------------------------------------------------

AlarmTableView = RSM.View({
  'alarms' : {'xpath':'alarm-summary/active-alarm-count', 'as_type': int },
  'list' : {'table' : RSM.Table('alarm-detail',
      key='alarm-short-description',
      view=RSM.View({
        'time' : {'xpath':'alarm-time'},
        'time_epoc' : {'xpath':'alarm-time/@seconds', 'as_type': int},
        'severity' : {'xpath':'alarm-class'},
        'type' : {'xpath':'alarm-type'},
        'description' : {'xpath':'alarm-description'},
        'brief' : {'xpath':'alarm-short-description'}
      })
    )}
  })

###> show system alarms

SysAlarmTable = RSM.TableGetter('get-system-alarm-information',
  key = None, view = AlarmTableView )

###> show chassis alarams

ChassisAlarmTable = RSM.TableGetter('get-alarm-information',
  key = None, view = AlarmTableView )