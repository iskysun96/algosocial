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
    following = Bytes("following")
    joined = Bytes("joined")

    handle_creation = Seq(
        Assert(
            And(
                Txn.application_args.length() == Int(6),
                Txn.application_args[2] == TealType.bytes,
                Txn.application_args[3] == TealType.uint64,
            ),
        ),
        App.globalPut(name, Txn.application_args[0]),
        App.globalPut(tag, Txn.application_args[1]),
        App.globalPut(wallet_addr, Txn.application_args[2]),
        App.globalPut(age, Txn.application_args[3]),
        App.globalPut(intro, Txn.application_args[4]),
        App.globalPut(twitter, Txn.application_args[5]),
        App.globalPut(donation, Int(0)),
        App.globalPut(follower, Int(0)),
        App.globalPut(following, Int(0)),
        App.globalPut(joined, Global.latest_timestamp()),
        Approve(),
    )

    handle_optin = Seq(
        # group txn. 
        # 1st: app cal the txn sender's contract to update their following count (on_following_update)
        # 2nd: update follower of this contract 
        # another solution
        # pass in app ID and then do inner transaction 
        # application args[0] = caller's app ID
        Assert(
            And(
                Txn.sender() != App.globalGet(wallet_addr),
                #compare hash of profile A and B TODO: change below code when nullun post guide
                AppParam.approvalProgram(Txn.applications[1]) == AppParam.approvalProgram(approval_program()),
            ),
        ),
        App.globalPut(follower, App.globalGet(follower) + Int(1)),
        Approve(),
    )

    on_follow = Seq(
        Assert(
                Txn.application_args.length() == Int(2),
        ),
        App.globalPut(following, App.globalGet(following) + Int(1)),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.on_completion: OnComplete.OptIn,
                TxnField.receiver: Txn.application_args[1]
            }
        ),
        InnerTxnBuilder.Submit(),
        Approve(),
    )

    handle_closeout = Seq(
        Assert(
            And(
                Txn.sender() != App.globalGet(wallet_addr),
                #TODO: change this code when nullun post guide
                AppParam.approvalProgram(Txn.applications[1]) == AppParam.approvalProgram(approval_program()),
            )
        ),
        App.globalPut(follower, App.globalGet(follower) - Int(1)), 
        Approve(),
    )

    on_unfollow = Seq(
        Assert(
            Txn.application_args.length() == Int(2),
        ),
        App.globalPut(following, App.globalGet(following) - Int(1)),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.on_completion: OnComplete.CloseOut,
                TxnField.receiver: Txn.application_args[1]
            }
        ),
        InnerTxnBuilder.Submit(),
        Approve(),
    )

    on_call_method = Txn.application_args[0]
    on_call = Cond(
        # Five conditions for NoOp
        [on_call_method == Bytes("update_info"), on_update_info],
        [on_call_method == Bytes("withdraw"), on_withdraw],
        [on_call_method == Bytes("donate"), on_donate],
        [on_call_method == Bytes("follow"), on_follow],
        [on_call_method == Bytes("unfollow"), on_unfollow],
    )

    on_update_info = Seq([
        # only profile owner can call this function
        Assert(
            And(
                Txn.sender() == App.globalGet("WalletAddr"),
                Txn.application_args.length() == Int(1),
            )
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

    on_donate_txn_index = Txn.group_index() - Int(1)

    on_donate = Seq(
        # when users donate
        # Grouped Txns
        # 1st: payment txn to contract
        # 2nd: app call

        Assert(
            And(
                Gtxn[on_donate_txn_index].type_enum() == TxnType.Payment,
                Gtxn[on_donate_txn_index].receiver() == Global.current_application_address(),
                Gtxn[on_donate_txn_index].amount() >= Global.min_txn_fee(),
            ),
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
                And(
                    Gtxn[on_donate_txn_index].sender() == App.globalGet(wallet_addr),
                    Gtxn[on_donate_txn_index].type_enum() == TxnType.Payment,
                    Gtxn[on_donate_txn_index].receiver() == wallet_global,
                    Gtxn[on_donate_txn_index].amount() <= donation_amt_global,
                ),
            ),
            App.globalPut(donation, donation_amt_global - Gtxn[on_donate_txn_index].amount()),
            Approve(),
        ),
        Reject(),
    )

    handle_updateapp = Reject()
    handle_deleteapp = Return(Int(1))
        
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