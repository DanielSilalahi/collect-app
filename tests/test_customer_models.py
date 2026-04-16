from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base
from models import activity_log, collection, customer_address, customer_contact, customer_import_row, customer_loan, user, va_data, va_request  # noqa: F401
from models.customer import Customer
from models.customer_loan import CustomerLoan


def test_customer_can_hold_current_loan_snapshot():
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        customer = Customer(
            full_name="Budi Santoso",
            platform_name="Partner A",
            status="new",
        )
        loan = CustomerLoan(
            customer=customer,
            is_current=1,
            loan_number="LN-001",
            total_outstanding=Decimal("1500000.00"),
            overdue_days=12,
        )

        customer.current_loan = loan
        customer.current_total_outstanding = loan.total_outstanding
        customer.current_dpd = loan.overdue_days

        session.add(customer)
        session.commit()
        customer_id = customer.id
        session.expunge_all()

        loaded_customer = session.get(Customer, customer_id)

        assert loaded_customer.current_loan.loan_number == "LN-001"
        assert loaded_customer.current_total_outstanding == Decimal("1500000.00")
        assert loaded_customer.current_dpd == 12
    finally:
        session.close()
