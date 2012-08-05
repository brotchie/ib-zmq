# Incoming message ids.
TICK_PRICE               = 1
TICK_SIZE                = 2
ORDER_STATUS             = 3
ERR_MSG                  = 4
OPEN_ORDER               = 5
ACCT_VALUE               = 6
PORTFOLIO_VALUE          = 7
ACCT_UPDATE_TIME         = 8
NEXT_VALID_ID            = 9
CONTRACT_DATA            = 10
EXECUTION_DATA           = 11
MARKET_DEPTH     	     = 12
MARKET_DEPTH_L2          = 13
NEWS_BULLETINS    	     = 14
MANAGED_ACCTS    	     = 15
RECEIVE_FA    	         = 16
HISTORICAL_DATA          = 17
BOND_CONTRACT_DATA       = 18
SCANNER_PARAMETERS       = 19
SCANNER_DATA             = 20
TICK_OPTION_COMPUTATION  = 21
TICK_GENERIC             = 45
TICK_STRING              = 46
TICK_EFP                 = 47
CURRENT_TIME             = 49
REAL_TIME_BARS           = 50
FUNDAMENTAL_DATA         = 51
CONTRACT_DATA_END        = 52
OPEN_ORDER_END           = 53
ACCT_DOWNLOAD_END        = 54
EXECUTION_DATA_END       = 55
DELTA_NEUTRAL_VALIDATION = 56
TICK_SNAPSHOT_END        = 57
MARKET_DATA_TYPE         = 58
COMMISSION_REPORT        = 59

FieldCount = 'FieldCount'
Done       = 'Done'

IB_MAX_DOUBLE = '1.7976931348623157E308'

def fixed(n):
    def parser(msgid, msgversion):
        fields = yield FieldCount, n
        yield Done, (msgid, msgversion) + fields
    return parser

def empty():
    def parser(msgid, msgversion):
        yield FieldCount, 0
        yield Done, (msgid, msgversion)
    return parser

def scannerdata(msgid, msgversion):
    data = yield FieldCount, 2
    if data[1] and int(data[1]):
        data += yield FieldCount, 16*int(data[1])
    yield Done, (msgid, msgversion) + data

def contractdata(msgid, msgversion):
    first = yield FieldCount, 29

    secids = yield FieldCount, 1
    if secids[0] and int(secids[0]):
        secids += yield FieldCount, 2*int(secids[0])

    yield Done, (msgid, msgversion) + first + secids

def bondcontractdata(msgid, msgversion):
    data = yield FieldCount, 30
    if data[29] and int(data[29]):
        data += yield FieldCount, 2*int(data[29])
    yield Done, (msgid, msgversion) + data

def historicaldata(msgid, msgversion):
    data = yield FieldCount, 4
    if data[3] and int(data[3]):
        data += yield FieldCount, 9*int(data[3])
    yield Done, (msgid, msgversion) + data

def openorders(msgid, msgversion):
    assert msgversion == 30, 'Only tested with version 30 of open orders message.'

    first = yield FieldCount, 58

    delta_neutral = yield FieldCount, 2
    if delta_neutral[0]:
        delta_neutral += yield FieldCount, 4

    second = yield FieldCount, 6

    combo_legs = yield FieldCount, 2
    if combo_legs[1] and int(combo_legs[1]):
        combo_legs += yield FieldCount, 8*int(combo_legs[1])

    order_combo_legs = yield FieldCount, 1
    if order_combo_legs[0] and int(order_combo_legs[0]):
        order_combo_legs += yield FieldCount, int(order_combo_legs[0])

    smart_combo_routing = yield FieldCount, 1
    if smart_combo_routing[0] and int(smart_combo_routing[0]):
        smart_combo_routing += yield FieldCount, 2*int(smart_combo_routing[0])

    scale = yield FieldCount, 3
    if scale[2] not in ('', '0.0', IB_MAX_DOUBLE):
        scale += yield FieldCount, 7

    hedge = yield FieldCount, 1
    if hedge[0]:
        hedge += yield FieldCount, 1

    third = yield FieldCount, 4

    undercomp = yield FieldCount, 1
    if undercomp[0] and int(undercomp[0]):
        undercomp += yield FieldCount, 3

    algo = yield FieldCount, 1
    if algo[0]:
        algos = yield FieldCount, 1
        if algos[0]:
            algos += yield FieldCount, 2*int(algos[0])
        algo += algos

    state = yield FieldCount, 10

    yield Done, ((msgid, msgversion) + 
                 first + delta_neutral +
                 second + combo_legs +
                 order_combo_legs +
                 smart_combo_routing +
                 scale + hedge + third +
                 undercomp + algo + state)

MESSAGE_PARSERS = {
    TICK_PRICE:               fixed(5),
    TICK_SIZE:                fixed(3),
    ORDER_STATUS:             fixed(10),
    ERR_MSG:                  fixed(3),
    OPEN_ORDER:               openorders,
    ACCT_VALUE:               fixed(4),
    PORTFOLIO_VALUE:          fixed(17),
    ACCT_UPDATE_TIME:         fixed(1),
    NEXT_VALID_ID:            fixed(1),
    CONTRACT_DATA:            contractdata,
    EXECUTION_DATA:           fixed(28),
    MARKET_DEPTH:             fixed(6),
    MARKET_DEPTH_L2:          fixed(7),
    NEWS_BULLETINS:           fixed(4),
    MANAGED_ACCTS:            fixed(1),
    RECEIVE_FA:               fixed(2),
    HISTORICAL_DATA:          historicaldata,
    BOND_CONTRACT_DATA:       bondcontractdata,
    SCANNER_PARAMETERS:       fixed(1),
    SCANNER_DATA:             scannerdata,
    TICK_OPTION_COMPUTATION:  fixed(10),
    TICK_GENERIC:             fixed(3),
    TICK_STRING:              fixed(3),
    TICK_EFP:                 fixed(9),
    CURRENT_TIME:             fixed(1),
    REAL_TIME_BARS:           fixed(9),
    FUNDAMENTAL_DATA:         fixed(2),
    CONTRACT_DATA_END:        fixed(1),
    OPEN_ORDER_END:           empty(),
    ACCT_DOWNLOAD_END:        fixed(1),
    EXECUTION_DATA_END:       fixed(1),
    DELTA_NEUTRAL_VALIDATION: fixed(4),
    TICK_SNAPSHOT_END:        fixed(1),
    MARKET_DATA_TYPE:         fixed(2),
    COMMISSION_REPORT:        fixed(6),
}
