from pydantic import BaseModel, Field, field_validator, model_validator
from decimal import Decimal
import re
from datetime import datetime
from typing import List, Optional


class UserData(BaseModel):
    beneName: str = Field(None, max_length=100, description="Beneficiary name")
    beneAccountNo: str = Field(
        ..., max_length=20, description="Account Number to be validated"
    )
    beneifsc: str = Field(..., description="Beneficiary bank IFSC code")
    benePhoneNo: int = Field(..., description="Mobile Number of beneficiary")
    beneBankName: str = Field(..., description="Bank name of the beneficiary")
    # clientReferenceNo: str = Field(..., min_length=12, max_length=22, description="Customer reference number")
    amount: Decimal = Field(
        ..., description="Amount to be transferred to the beneficiary"
    )
    fundTransferType: str = Field(..., description="Mode of payment (IMPS/NEFT)")
    pincode: int = Field(..., description="Pin code of the transaction initiator")
    custName: str = Field(..., max_length=25, description="Name of the customer")
    custMobNo: int = Field(..., description="Mobile Number of customer")
    # custIpAddress: str = Field(..., description="Customer IP Address")
    # latlong: str = Field(
    #     ...,
    #     max_length=22,
    #     description="Latitude longitude of the transaction initiator",
    # )
    paramA: Optional[str] = Field(
        None, description="To be used as per client's discretion"
    )
    paramB: Optional[str] = Field(
        None, description="To be used as per client's discretion"
    )


class TransactionRequest(BaseModel):
    access_token: str
    token_type: str
    user_data: UserData

    @field_validator("user_data", mode="before")
    def parse_amount(cls, value):
        if isinstance(value.get("amount"), float):
            value["amount"] = Decimal(str(value["amount"]))
        return value

    @field_validator("access_token", "token_type")
    def clean_data(cls, v):
        if isinstance(v, str):
            v = v.strip()
        return v

    # Account number validator
    @field_validator("user_data")
    def account_number_max_20_digits(cls, v):
        match = re.match(r"^\d{1,20}$", v.beneAccountNo)
        if match is None:
            raise ValueError("Beneficiary Account Number should be max 20 digits")
        return v

    # Phone number validator
    @field_validator("user_data")
    def beneficiary_phone_validation(cls, v):
        v.benePhoneNo = str(v.benePhoneNo)
        regex = r"^[6789]\d{9}$"
        if v.benePhoneNo and not re.search(regex, v.benePhoneNo, re.I):
            raise ValueError("Invalid beneficiary Phone Number Invalid.")
        return v

    # Phone number validator
    @field_validator("user_data")
    def customer_phone_validation(cls, v):
        v.custMobNo = str(v.custMobNo)
        regex = r"^[6789]\d{9}$"
        if v.custMobNo and not re.search(regex, v.custMobNo, re.I):
            raise ValueError("Invalid customer Phone Number Invalid.")
        return v

    @field_validator("user_data")
    def ifsc_code_validation(cls, v):
        if len(v.beneifsc) > 11:
            raise ValueError("IFSC code should be maximum 11 digits only")
        return v

    @field_validator("user_data")
    def pin_code_validation(cls, v):
        v.pincode = str(v.pincode)
        if len(v.pincode) > 6:
            raise ValueError("Pin code should be maximum 6 digits only")
        return v


class TransactionResponse(BaseModel):
    status: str
    subStatus: str
    statusDesc: str
    rrn: str
    transactionId: int
    beneName: str
    beneAccountNo: str
    beneifsc: str
    benePhoneNo: str
    beneBankName: str
    clientReferenceNo: str
    txnAmount: float
    txnType: str
    latlong: str
    pincode: str
    custName: str
    custMobNo: str
    dateTime: str
    paramA: Optional[str] = None
    paramB: Optional[str] = None


class UserStatusData(BaseModel):
    Query_Operation: str = Field(
        ...,
        description="Hard-coded field. Must pass the value provided in E.g. It must not be NULL.",
        example="Cashout_addbank_status",
    )

    Start_Date: str = Field(
        ...,
        description="Date field in yyyy-mm-dd format pass in string. It must not be NULL. It must be the same as the End Date.",
        example="2023-03-23",
    )

    End_Date: str = Field(
        ...,
        description="Date field in yyyy-mm-dd format pass in string. It must not be NULL. It must be the same as the Start Date.",
        example="2023-03-23",
    )

    ClientRefId: str = Field(
        ...,
        description="Client Reference ID. Length = 15 It must not be NULL.",
        example="123456789012345",
    )

    Transaction_ID: str = Field(
        None, description="Transaction ID. Length ≤ 20.", example="871502989336576"
    )


class StatusRequest(BaseModel):
    access_token: str
    token_type: str
    user_status_data: UserStatusData

    @classmethod
    @field_validator("user_status_data")
    def validate_client_ref_id(cls, v):
        if v and len(v.ClientRefId) != 15:
            raise ValueError("Client Reference ID should be 15 digits long.")
        return v

    @classmethod
    @field_validator("user_status_data")
    def validate_transaction_id(cls, v):
        if v and len(v.Transaction_ID) > 20:
            raise ValueError("Transaction ID length should be at most 20 characters")
        return v

    @classmethod
    @field_validator("user_status_data")
    def start_date_matches_end_date(cls, v):
        if v.Start_Date != v.End_Date:
            raise ValueError("Start Date must be the same as the End Date")
        return v

    @classmethod
    @field_validator("user_status_data")
    def end_date_matches_start_date(cls, v, values):
        if v.End_Date != values["user_status_data"].Start_Date:
            raise ValueError("End Date must be the same as the Start Date")
        return v


class TransactionResult(BaseModel):
    transactionId: int
    subStatus: int
    status: str
    statusDesc: str
    beneName: str
    beneAccountNo: str
    beneifsc: str
    benePhoneNo: int
    beneBankName: str
    clientReferenceNo: str
    latlong: str
    pincode: int
    custName: str
    custMobNo: int
    rrn: str
    paramA: str = None
    paramB: str = None
    dateTime: str
    txnAmount: Decimal
    txnType: str


class StatusResponse(BaseModel):
    status: int
    message: str
    length: int
    results: List[TransactionResult]

    @field_validator("results", mode="before")
    def parse_amounts(cls, value):
        for result in value:
            if isinstance(result.get("txnAmount"), float):
                result["txnAmount"] = Decimal(str(result["txnAmount"]))
        return value


class StatusErrorResponse(BaseModel):
    status: int
    message: str


class Balancerequest(BaseModel):
    access_token: str
    token_type: str
