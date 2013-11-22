from . import RunstatMaker as RSM

##### -------------------------------------------------------------------------
##### nice illustration of using the same View on different Tables
##### -------------------------------------------------------------------------

AlarmTableView = RSM.View(RSM.Fields()
  .int('count', 'alarm-summary/active-alarm-count')
  .table('list', RSM.Table('alarm-detail',
    key='alarm-short-description',
    view=RSM.View(RSM.Fields()
      .str('time','alarm-time')
      .int('time_epoc', 'alarm-time/@seconds')
      .str('severity''alarm-class')
      .str('type''alarm-type')
      .str('description','alarm-description')
      .str('brief','alarm-short-description')
      .end))
  )
  .end
)

###> show system alarms

SysAlarmTable = RSM.GetTable('get-system-alarm-information',
  key = None, view = AlarmTableView )

###> show chassis alarams

ChassisAlarmTable = RSM.GetTable('get-alarm-information',
  key = None, view = AlarmTableView )