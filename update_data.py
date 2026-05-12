from data_scripts.calls_data import update_call_logs
from data_scripts.applications_data import update_app_sold
from data_scripts.responses_data import update_response_creation, update_shortlist_responses, update_base_course_mapping
from data_scripts.fresh_leads_data import fetch as update_fresh_leads
from data_scripts.allocation_data import fetch_counselling_allocations as update_allocations


def _run(label, fn):
    print(f"\n=== {label} ===")
    try:
        fn()
    except Exception as e:
        print(f"  ERROR: {e}")


def main():
    _run("Step 1: Updating Call Logs",            update_call_logs)
    _run("Step 2: Updating Applications Sold",     update_app_sold)
    _run("Step 3.1: Updating Response Creation",   update_response_creation)
    _run("Step 3.2: Updating Shortlist Responses", update_shortlist_responses)
    _run("Step 3.3: Updating Base Course Mapping", update_base_course_mapping)
    _run("Step 4: Updating Fresh Leads",           update_fresh_leads)
    _run("Step 5: Updating Allocations",           update_allocations)


if __name__ == "__main__":
    main()
