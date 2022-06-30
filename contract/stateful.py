from pyteal import *

def approval_program():

    """
    Social Profile
    Global state
    - Name / ID
    - tag
    - wallet address
    - Age
    - introduction
    - twitter url
    - when joined 
    """
    handle_creation = Seq([
        Assert(
            And(
                Txn.application_args.length() == Int(7),
                Txn.application_args[2] == TealType.bytes,
                Txn.application_args[3] == TealType.uint64,
            )
        ),
        App.globalPut(Bytes("Name"), Txn.application_args[0]),
        App.globalPut(Bytes("Tag"), Txn.application_args[1]),
        App.globalPut(Bytes("WalletAddr"), Txn.application_args[2]),
        App.globalPut(Bytes("Age"), Txn.application_args[3]),
        App.globalPut(Bytes("Intro"), Txn.application_args[4]),
        App.globalPut(Bytes("Twitter"), Txn.application_args[5]),
        App.globalPut(Bytes("Joined"), Global.latest_timestamp()),
        Approve(),
    ])

    handle_optin = Return(Int(1))

    handle_closeout = Return(Int(1))

    handle_updateapp = Seq([
        """
        only profile owner can call this function

        """,
        Assert(
            Txn.sender() == App.globalGet("WalletAddr"),
            Txn.application_args.length() == Int(1),
        ),
        If(Txn.application_args[0] == Bytes("Name")).Then(
            App.globalPut(Bytes("Name"), Txn.application_args[1]),
        ),
        If(Txn.application_args[0] == Bytes("Tag")).Then(
            App.globalPut(Bytes("Tag"), Txn.application_args[1]),
        ),
        If(Txn.application_args[0] == Bytes("WalletAddr")).Then(
            App.globalPut(Bytes("WalletAddr"), Txn.application_args[1]),
        ),
        If(Txn.application_args[0] == Bytes("Age")).Then(
            App.globalPut(Bytes("Age"), Txn.application_args[1]),
        ),
        If(Txn.application_args[0] == Bytes("Intro")).Then(
            App.globalPut(Bytes("Intro"), Txn.application_args[1]),
        ),
        If(Txn.application_args[0] == Bytes("Joined")).Then(
            Reject()
        ),
        Approve(),
    ])

    handle_deleteapp = Return(Int(1))

    handle_noop = Seq(
        "followers update",
        Assert(Global.group_size() == Int(1)), 
        Cond(
            [Txn.application_args[0] == Bytes("Add"), add], 
            [Txn.application_args[0] == Bytes("Deduct"), deduct]
        )
    )

    program = Cond(
        [Txn.application_id() == Int(0), handle_creation],
        [Txn.on_completion() == OnComplete.OptIn, handle_optin],
        [Txn.on_completion() == OnComplete.CloseOut, handle_closeout],
        [Txn.on_completion() == OnComplete.UpdateApplication, handle_updateapp],
        [Txn.on_completion() == OnComplete.DeleteApplication, handle_deleteapp],
        [Txn.on_completion() == OnComplete.NoOp, handle_noop]
    )

    return compileTeal(program, Mode.Application, version=5)

def clear_state_program():
    return 1
