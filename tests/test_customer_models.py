from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base
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
        session.expunge_all()

        loaded_customer = session.get(Customer, customer.id)

        assert loaded_customer.current_loan.loan_number == "LN-001"
        assert loaded_customer.current_total_outstanding == Decimal("1500000.00")
        assert loaded_customer.current_dpd == 12
    finally:
        session.close()
