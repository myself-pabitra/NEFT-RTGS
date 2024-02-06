from pydantic import BaseModel, Field, field_validator, model_validator
import re
from datetime import datetime
from typing import List


class TransactionRequest(BaseModel):
    beneName: str = Field(None, max_length=100, description="Beneficiary name")
    beneAccountNo: str = Field(
        ..., max_length=20, description="Account Number to be validated"
    )
    beneifsc: str = Field(..., description="Beneficiary bank IFSC code")
    benePhoneNo: int = Field(..., description="Mobile Number of beneficiary")
    beneBankName: str = Field(..., description="Bank name of the beneficiary")
    # clientReferenceNo: str = Field(..., min_length=12, max_length=22, description="Customer reference number")
    amount: int = Field(..., description="Amount to be transferred to the beneficiary")
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
    paramA: str = Field(None, description="To be used as per client's discretion")
    paramB: str = Field(None, description="To be used as per client's discretion")

    @field_validator("*", mode="before")
    def clean_data(cls, v):
        if isinstance(v, str):
            # Example: Remove leading and trailing whitespaces
            v = v.strip()
        return v

    # Account number validator
    @field_validator("beneAccountNo")
    def account_number_max_20_digits(cls, v):
        match = re.match(r"^\d{1,20}$", v)
        if match is None:
            raise ValueError("Beneficiary Account Number should be max 20 digits")
        return v

    # Phone number validator
    @field_validator("benePhoneNo")
    def beneficiary_phone_validation(cls, v):
        v = str(v)
        regex = r"^[6789]\d{9}$"
        if v and not re.search(regex, v, re.I):
            raise ValueError("Invalid beneficiary  Phone Number Invalid.")
        return v

    # Phone number validator
    @field_validator("custMobNo")
    def customer_phone_validation(cls, v):
        v = str(v)
        regex = r"^[6789]\d{9}$"
        if v and not re.search(regex, v, re.I):
            raise ValueError("invalud customer Phone Number Invalid.")
        return v

    @field_validator("beneifsc")
    def ifsc_code_validation(cls, v):

        if len(v) > 11:
            raise ValueError("IFSC code should be maximum 11 digits only")
        return v

    @field_validator("pincode")
    def pin_code_validation(cls, v):
        v = str(v)
        if len(v) > 6:
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
    txnAmount: int
    txnType: str
    latlong: str
    pincode: str
    custName: str
    custMobNo: str
    dateTime: str
    paramA: str = None
    paramB: str = None


class StatusRequest(BaseModel):
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

    @field_validator("ClientRefId")
    def validate_client_ref_id(cls, v):
        if v and len(v) != 15:
            raise ValueError("Client Reference ID should be 15 digits of long..")
        return v

    @field_validator("Transaction_ID")
    def validate_transaction_id(cls, v):
        if v and len(v) > 20:
            raise ValueError("Transaction ID length should be at most 20 characters")
        return v

    @field_validator("Start_Date")
    def start_date_matches_end_date(cls, v, values):
        end_date = values.data.get("End_Date")  # Access using values.data
        if end_date and v != end_date:
            raise ValueError("Start Date must be the same as the End Date")
        return v

    @field_validator("End_Date")
    def end_date_matches_start_date(cls, v, values):
        start_date = values.data.get("Start_Date")  # Access using values.data
        if start_date and v != start_date:
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
    txnAmount: int
    txnType: str


class StatusResponse(BaseModel):
    status: int
    message: str
    length: int
    results: List[TransactionResult]


class StatusErrorResponse(BaseModel):
    status: int
    message: str


#     {
#     "beneName": "Rajesh Kumar Nayak",
#     "beneAccountNo": "33171402473",
#     "beneifsc": "SBIN0001083",
#     "benePhoneNo": 7381279922,
#     "beneBankName": "State Bank of India",
#     "clientReferenceNo": "22345231232231",
#     "amount": 100,
#     "fundTransferType":"IMPS",
#     "pincode":751024,
#     "custName":"Vijay Nayak",
#     "custMobNo":9821361027,
#     "custIpAddress": "49.249.100.78",
#     "latlong": "22.8031731,88.7874172",
#     "paramA": "",
#     "paramB": ""
# }


# {
#     "beneName": "Pabitra Pandit",
#     "beneAccountNo": "38183275000",
#     "beneifsc": "SBIN0009710",
#     "benePhoneNo": 8158079208,
#     "beneBankName": "State Bank of India",
#     "amount": 18000,
#     "fundTransferType":"IMPS",
#     "pincode":721140,
#     "custName":"Vijay Nayak",
#     "custMobNo":9821361027,
#     "paramA": "",
#     "paramB": ""
# }
