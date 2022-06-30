from pyteal import *

def approval_program():

    # Social Profile
    # Global state
    # - Name / ID
    # - tag
    # - wallet address
    # - Age
    # - introduction
    # - twitter url
    # - donation
    # - when joined 

    name = Bytes("name")
    tag = Bytes("tag")
    wallet_addr = Bytes("wallet_addr")
    age = Bytes("age")
    intro = Bytes("intro")
    twitter = Bytes("twitter")
    donation = Bytes("donation")
    follower = Bytes("follower")
    joined = Bytes("joined")

    handle_creation = Seq(
        Assert(
            And(
                Txn.application_args.length() == Int(8),
                Txn.application_args[2] == TealType.bytes,
                Txn.application_args[3] == TealType.uint64,
            )
        ),
        App.globalPut(name, Txn.application_args[0]),
        App.globalPut(tag, Txn.application_args[1]),
        App.globalPut(wallet_addr, Txn.application_args[2]),
        App.globalPut(age, Txn.application_args[3]),
        App.globalPut(intro, Txn.application_args[4]),
        App.globalPut(twitter, Txn.application_args[5]),
        App.globalPut(donation, Int(0)),
        App.globalPut(follower, Int(0)),
        App.globalPut(joined, Global.latest_timestamp()),
        Approve(),
    )

    # @Subroutine(TealType.none)
    # def withdraw(account: Expr, amount: Expr) -> Expr:
    #     return Seq(
    #         InnerTxnBuilder.Begin(),
    #         InnerTxnBuilder.SetFields(
    #             {
    #                 TxnField.type_enum: TxnType.Payment,
    #                 TxnField.amount: amount,
    #                 TxnField.receiver: account
    #             }
    #         ),
    #         InnerTxnBuilder.Submit(),
    #     )

    # @Subroutine(TealType.none)
    # def donate(amount: Expr) -> Expr:
    #     return Seq(
    #         InnerTxnBuilder.Begin(),
    #         InnerTxnBuilder.SetFields(
    #             {
    #                 TxnField.type_enum: TxnType.Payment,
    #                 TxnField.amount: amount,

    #             }
    #         )
    #     )

    handle_optin = Return(Int(1))

    handle_closeout = Return(Int(1))

    handle_deleteapp = Return(Int(1))

    on_call_method = Txn.application_args[0]
    on_call = Cond(
        [on_call_method == Bytes("update_info"), on_update_info],
        [on_call_method == Bytes("follower"), on_follower_update],
        [on_call_method == Bytes("withdraw"), on_withdraw],
        [on_call_method == Bytes("donate"), on_donate],
    )

    on_update_info = Seq([
        # only profile owner can call this function
        Assert(
            Txn.sender() == App.globalGet("WalletAddr"),
            Txn.application_args.length() == Int(1),
        ),
        If(Txn.application_args[0] == name).Then(
            App.globalPut(name, Txn.application_args[1]),
        ),
        If(Txn.application_args[0] == tag).Then(
            App.globalPut(tag, Txn.application_args[1]),
        ),
        If(Txn.application_args[0] == wallet_addr).Then(
            App.globalPut(wallet_addr, Txn.application_args[1]),
        ),
        If(Txn.application_args[0] == age).Then(
            App.globalPut(age, Txn.application_args[1]),
        ),
        If(Txn.application_args[0] == intro).Then(
            App.globalPut(intro, Txn.application_args[1]),
        ),
        If(Txn.application_args[0] == donation).Then(
            Reject(),
        ),
        If(Txn.application_args[0] == twitter).Then(
            App.globalPut(twitter, Txn.application_args[1]),
        ),
        If(Txn.application_args[0] == follower).Then(
            Reject(),
        ),
        If(Txn.application_args[0] == joined).Then(
            Reject(),
        ),
        Approve(),
    ])

    on_follower_update = Seq(
        "followers update (TODO)",
        Assert(
            Txn.sender() != App.globalGet(wallet_addr),
        ),
        If(Txn.application_args[0] == Bytes("follow")).Then(
            App.globalPut(follower, App.globalGet(follower) + Int(1)),
        ),
        If(Txn.application_args[0] == Bytes("unfollow")).Then(
            App.globalPut(follower, App.globalGet(follower) - Int(1)),
        ), 
        Approve(),
    )

    on_donate_txn_index = Txn.group_index() - Int(1)

    on_donate = Seq(
        # when users donate
        # Grouped Txns
        # 1st: payment txn to contract
        # 2nd: app call

        Assert(
            Gtxn[on_donate_txn_index].type_enum() == TxnType.Payment,
            Gtxn[on_donate_txn_index].receiver() == Global.current_application_address(),
            Gtxn[on_donate_txn_index].amount() >= Global.min_txn_fee(),
        ),
        App.globalPut(donation, App.globalGet(donation) + Gtxn[on_donate_txn_index].amount()),
        Approve(),
    )

    wallet_global = App.globalGet(wallet_addr)
    donation_amt_global = App.globalGet(donation)

    on_withdraw = Seq(
        # withdraw donation
        # grouped txn
        # 1st: payment txn from contract to caller
        # 2nd: app call

        wallet_global,
        donation_amt_global,
        If(App.globalGet(donation_amt_global) > Int(0)).Then(
            Assert(
                Gtxn[on_donate_txn_index].sender() == App.globalGet(wallet_addr),
                Gtxn[on_donate_txn_index].type_enum() == TxnType.Payment,
                Gtxn[on_donate_txn_index].receiver() == wallet_global,
                Gtxn[on_donate_txn_index].amount() <= donation_amt_global,
            ),
            App.globalPut(donation, donation_amt_global - Gtxn[on_donate_txn_index].amount()),
            Approve(),
        ),
        Reject(),
    )

        
    program = Cond(
        [Txn.application_id() == Int(0), handle_creation],
        [Txn.on_completion() == OnComplete.OptIn, handle_optin],
        [Txn.on_completion() == OnComplete.CloseOut, handle_closeout],
        [Txn.on_completion() == OnComplete.UpdateApplication, handle_updateapp],
        [Txn.on_completion() == OnComplete.DeleteApplication, handle_deleteapp],
        [Txn.on_completion() == OnComplete.NoOp, on_call]
    )

    return program

def clear_state_program():
    return Approve()


if __name__ == "__main__":
    with open("auction_approval.teal", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=5)
        f.write(compiled)

    with open("auction_clear_state.teal", "w") as f:
        compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=5)
        f.write(compiled)