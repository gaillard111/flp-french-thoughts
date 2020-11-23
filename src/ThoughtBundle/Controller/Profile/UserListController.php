<?php

namespace ThoughtBundle\Controller\Profile;

use Application\Sonata\UserBundle\Entity\User;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;

class UserListController extends Controller
{
    /**
     * @Route("/users", name="user_list")
     * @param Request $request
     * @return Response
     */
    public function userListAction(Request $request)
    {
        $this->denyAccessUnlessGranted('IS_AUTHENTICATED_FULLY');
        $userRepository = $this->getDoctrine()->getRepository(User::class);
        $role = $this->getUser()->getRole();

        if ($role == User::ROLE_STUDENT or $role == User::ROLE_TEACHER) {
            $usersQuery = $userRepository->getStudentAndTeacherQuery();
        } else {
            $usersQuery = $userRepository->getStandardUsersQuery();
        }

        $paginator  = $this->get('knp_paginator');
        $pagination = $paginator->paginate(
            $usersQuery,
            $request->query->getInt('page', 1),
            30
        );

        return $this->render('@Thought/Profile/users_list/users_list.html.twig', [
            'users' => $pagination,
        ]);
    }

    /**
     * @Route("/students/list", name="students_list")
     * @param Request $request
     * @return Response
     */
    public function studentList(Request $request)
    {
        $this->denyAccessUnlessGranted(['ROLE_TEACHER', 'ROLE_ADMIN'], null, 'Unable to access this page!');
        $userRepository = $this->getDoctrine()->getRepository(User::class);

        $studentsQuery = $userRepository->getAllStudentsQuery();

        $paginator  = $this->get('knp_paginator');
        $paginationStudents = $paginator->paginate(
            $studentsQuery,
            $request->query->getInt('page', 1),
            20
        );

        return $this->render('@Thought/Profile/users_list/students_list.html.twig', [
            'students' => $paginationStudents,
        ]);
    }

    /**
     * @Route("/teachers/list", name="teachers_list")
     * @param Request $request
     * @return Response
     */
    public function teachersList(Request $request)
    {
        $this->denyAccessUnlessGranted(['ROLE_ADMIN'], null, 'Unable to access this page!');
        $userRepository = $this->getDoctrine()->getRepository(User::class);

        $teachersQuery = $userRepository->getAllTeachersQuery();

        $paginator  = $this->get('knp_paginator');
        $paginationTeachers = $paginator->paginate(
            $teachersQuery,
            $request->query->getInt('page', 1),
            20
        );

        return $this->render('@Thought/Profile/users_list/teachers_list.twig', [
            'teachers' => $paginationTeachers,
        ]);
    }
}