<?php

namespace ThoughtBundle\Controller\Profile;

use Sensio\Bundle\FrameworkExtraBundle\Configuration\ParamConverter;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\Routing\Annotation\Route;
use ThoughtBundle\Entity\TeacherGroup;

/**
 * @Route("/profile")
 */
class StudentPageController extends Controller
{
    /**
     * @Route("/my_groups", name="my_groups")
     */
    public function listGroup() {
        $this->denyAccessUnlessGranted('ROLE_STUDENT');
        $myGroups = $this->getUser()->getTeacherGroup();
        return $this->render('@Thought/Profile/Student/group_list.html.twig', [
            'groups' => $myGroups
        ]);
    }

    /**
     * @Route("/my_group/{groupId}", name="my_group")
     * @ParamConverter("group", options={"mapping"={"groupId"="id"}})
     */
    public function group(TeacherGroup $group) {
        $this->denyAccessUnlessGranted('ROLE_STUDENT');
        return $this->render('@Thought/Profile/Student/group.html.twig', [
            'group' => $group
        ]);
    }
}