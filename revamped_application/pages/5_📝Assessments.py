import streamlit as st

from core.assessments.create_assessment import CreateAssessment
from core.assessments.update_void_assessment import UpdateVoidAssessment
from core.assessments.view_assessment import ViewAssessment
from core.constants import GRADES, RESULTS, ID_TYPE, ASSESSMENT_UPDATE_VOID_ACTIONS
from core.models.assessments import CreateAssessmentInfo, UpdateVoidAssessmentInfo
from utils.http_utils import handle_error
from utils.streamlit_utils import init, display_config

init()

st.set_page_config(page_title="Assessments", page_icon="📝")

with st.sidebar:
    if st.button("Configs", key="config_display"):
        display_config()

st.header("Assessments")
st.markdown("The Assessments API allows you to create, update, void, find and view assessments that are "
            "assigned to your trainees in your courses!")

create, update_void, find, view = st.tabs([
    "Create Assessment", "Update/Void Assessment", "Find Assessment", "View Assessment"
])

with create:
    st.header("Create Assessment")
    st.markdown("You can use this API to create an assessment record for trainees enrolled in your courses.")

    create_assessment_info = CreateAssessmentInfo()
    st.subheader("Course Info")
    create_assessment_info.set_course_runId(st.text_input(label="Enter the Course Run ID",
                                                          max_chars=20,
                                                          key="create-assessment-run-id"))
    create_assessment_info.set_course_referenceNumber(st.text_input(label="Enter the Course Reference Number",
                                                                    max_chars=100,
                                                                    key="create-assessment-reference-number"))

    st.subheader("Trainee Info")
    create_assessment_info.set_trainee_id(st.text_input(label="Enter the Trainee ID Number",
                                                        max_chars=20,
                                                        key="create-assessment-trainee-id"))
    create_assessment_info.set_trainee_id_type(st.selectbox(label="Enter the Trainee ID Type",
                                                            options=ID_TYPE,
                                                            key="create-assessment-trainee-id-type"))
    create_assessment_info.set_trainee_fullName(st.text_input(label="Enter the Trainee Full Name",
                                                              max_chars=200,
                                                              key="create-assessment-trainee-full-name"))

    st.subheader("Assessment Info")
    if st.checkbox("Specify Grade?", key="create-grade"):
        create_assessment_info.set_grade(st.selectbox(label="Select Grade",
                                                      options=GRADES,
                                                      key="create-assessment-grade"))

    if st.checkbox("Specify Score?", key="create-score"):
        create_assessment_info.set_score(st.number_input(label="Select Score",
                                                         min_value=0,
                                                         step=0.1,
                                                         key="create-assessment-score"))

    if st.checkbox("Specify Skill Code?", key="create-assessment-skill-code"):
        create_assessment_info.set_skillCode(st.text_input(label="Enter the Skill Code",
                                                           max_chars=30,
                                                           key="create-assessment-skill-code"))

    if st.checkbox("Specify Conferring Institute Code?", key="create-assessment-conferring-institute-code"):
        create_assessment_info.set_conferringInstitute_code(st.text_input(label="Enter the Conferring Institute Code",
                                                                          help="This field refers to the UEN/branch "
                                                                               "code of the supporting assessment TP "
                                                                               "for the results. If left blank, the "
                                                                               "trainingProvider.code is set as the "
                                                                               "default value!"))

    create_assessment_info.set_result(st.selectbox(label="Select Result",
                                                   options=RESULTS,
                                                   key="create-assessment-result"))
    create_assessment_info.set_assessmentDate(st.date_input(label="Select Assessment Date",
                                                            key="create-assessment-date"))
    create_assessment_info.set_trainingPartner_code(st.text_input(label="Enter the Training Partner Code",
                                                                  max_chars=12,
                                                                  key="create-assessment-training-partner-code"))

    st.divider()
    st.subheader("Preview Request Body")
    with st.expander("Request Body"):
        st.json(create_assessment_info.payload(verify=False))

    st.subheader("Send Request")
    st.markdown("Click the `Send` button below to send the request to the API!")

    if st.button("Send", key="edit-button"):
        errors = create_assessment_info.validate()

        if errors is not None:
            st.error(
                "Some errors are detected with your inputs:\n\n- " + "\n- ".join(errors)
            )
        else:
            request, response = st.tabs(["Request", "Response"])

            ec = CreateAssessment(create_assessment_info)

            with request:
                st.subheader("Request")
                st.code(repr(ec), language="text")

            with response:
                st.subheader("Response")
                handle_error(lambda: ec.execute())

with update_void:
    st.header("Update/Void Assessment")
    st.markdown("You can use this API to update or void an assessment record for trainees enrolled in your courses.")

    update_void_assessment = UpdateVoidAssessmentInfo()
    update_void_assessment.set_action(st.selectbox(label="Select Action to Perform",
                                                   options=ASSESSMENT_UPDATE_VOID_ACTIONS,
                                                   format_func=lambda x: x.upper(),
                                                   key="update-void-assessment-action"))

    st.subheader("Course Info")
    update_void_assessment.set_course_referenceNumber(st.text_input(label="Enter the Course Reference Number",
                                                                    max_chars=100,
                                                                    key="update-void-assessment-reference-number"))

    if update_void_assessment.is_update():
        st.subheader("Trainee Info")
        if st.checkbox("Update Trainee Full Name?", key="update-void-trainee-info"):
            update_void_assessment.set_trainee_fullName(st.text_input(label="Enter the Trainee Full Name",
                                                                      max_chars=200,
                                                                      key="update-void-assessment-trainee-full-name"))

        st.subheader("Assessment Info")
        if st.checkbox("Update Grade?", key="update-void-grade"):
            update_void_assessment.set_grade(st.selectbox(label="Select Grade",
                                                          options=GRADES,
                                                          key="update-void-assessment-grade"))

        if st.checkbox("Update Score?", key="update-void-score"):
            update_void_assessment.set_score(st.number_input(label="Select Score",
                                                             min_value=0.0,
                                                             step=0.1,
                                                             value=0.0,
                                                             format="%.1f",
                                                             key="update-void-assessment-score"))

        if st.checkbox("Update Skill Code?", key="will-update-void-assessment-skill-code"):
            update_void_assessment.set_skillCode(st.text_input(label="Enter the Skill Code",
                                                               max_chars=30,
                                                               key="update-void-assessment-skill-code"))

        if st.checkbox("Update Assessment Result?", key="update-void-assessment-results"):
            update_void_assessment.set_result(st.selectbox(label="Select Result",
                                                           options=RESULTS,
                                                           key="update-void-assessment-result"))

        if st.checkbox("Update Assessment Date?", key="will-update-void-assessment-date"):
            update_void_assessment.set_assessmentDate(st.date_input(label="Select Assessment Date",
                                                                    key="update-void-assessment-date"))

    st.divider()
    st.subheader("Preview Request Body")
    with st.expander("Request Body"):
        st.json(update_void_assessment.payload(verify=False))

    st.subheader("Send Request")
    st.markdown("Click the `Send` button below to send the request to the API!")

    if st.button("Send", key="update-void-button"):
        errors = update_void_assessment.validate()

        if errors is not None:
            st.error(
                "Some errors are detected with your inputs:\n\n- " + "\n- ".join(errors)
            )
        else:
            request, response = st.tabs(["Request", "Response"])

            uva = UpdateVoidAssessment(update_void_assessment)

            with request:
                st.subheader("Request")
                st.code(repr(uva), language="text")

            with response:
                st.subheader("Response")
                handle_error(lambda: uva.execute())
with find:
    pass

with view:
    st.header("View Assessment")
    st.markdown("You can use this API to view an assessment record for trainees enrolled in your courses.")

    arn = st.text_input(label="Enter the Assessment Reference Number",
                        max_chars=100,
                        key="view-assessment-reference-number")

    st.divider()
    st.subheader("Send Request")
    st.markdown("Click the `Send` button below to send the request to the API!")

    if st.button("Send", key="view-assessment-button"):
        if arn is None:
            st.error("Please enter the Assessment Reference Number")
        else:
            request, response = st.tabs(["Request", "Response"])

            va = ViewAssessment(arn)

            with request:
                st.subheader("Request")
                st.code(repr(va), language="text")

            with response:
                st.subheader("Response")
                handle_error(lambda: va.execute())
